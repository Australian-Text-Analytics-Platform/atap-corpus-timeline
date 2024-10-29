import logging
import traceback
from typing import Optional

import panel
import panel as pn
from atap_corpus.corpus.corpus import DataFrameCorpus
from atap_corpus_loader import CorpusLoader
from pandas import DataFrame, Series, Grouper
from pandas.core.dtypes.common import is_datetime64_any_dtype
from panel.pane import Plotly
from panel.widgets import Select, DatetimeRangePicker, Button, IntInput
import plotly.express as px

pn.extension("plotly")


class CorpusVisualiser(pn.viewable.Viewer):
    TIME_PERIOD_GROUPINGS: dict[str, str] = {
        'years': 'Y', 'quarters': 'Q', 'months': 'M',
        'weeks': 'W', 'days': 'D', 'hours': 'h',
        'minutes': 'min', 'seconds': 's'
    }
    TIME_PERIOD_INVERSE_GROUPINGS: dict[str, str] = {v: k for k, v in TIME_PERIOD_GROUPINGS.items()}

    CONTROLS_MAX_WIDTH: int = 120

    def log(self, msg: str, level: int):
        logger = logging.getLogger(self.logger_name)
        logger.log(level, msg)

    def __init__(self, corpus_loader: CorpusLoader, logger_name: str, **params):
        super().__init__(**params)
        self.corpus_loader: CorpusLoader = corpus_loader
        self.logger_name: str = logger_name

        self.corpus_selector = Select(name="Selected corpus", width=self.CONTROLS_MAX_WIDTH)
        self.time_col_selector = Select(name="Datetime column", width=self.CONTROLS_MAX_WIDTH)
        self.date_range_picker = DatetimeRangePicker(name="Datetime range", width=self.CONTROLS_MAX_WIDTH)
        self.date_group_periods = IntInput(name="Number of intervals", start=1, value=1, width=self.CONTROLS_MAX_WIDTH)
        self.date_group_unit_selector = Select(name="Intervals", options=self.TIME_PERIOD_GROUPINGS, width=self.CONTROLS_MAX_WIDTH)
        self.included_meta_selector = Select(name="Included metadata", width=self.CONTROLS_MAX_WIDTH)
        self.generate_plots_button = Button(name="Generate plot", button_style='solid', button_type='primary', width=self.CONTROLS_MAX_WIDTH)
        self.controls = pn.Column(
            self.corpus_selector,
            self.time_col_selector,
            self.date_range_picker,
            self.date_group_periods,
            self.date_group_unit_selector,
            self.included_meta_selector,
            self.generate_plots_button,
            width=self.CONTROLS_MAX_WIDTH
        )

        self.plots = pn.Column(min_width=1000, sizing_mode='stretch_width')

        self.panel = pn.Row(
            self.controls,
            self.plots,
            sizing_mode='stretch_width'
        )

        self.corpus_selector.param.watch(self._update_selected_corpus, ['value'])
        self.time_col_selector.param.watch(self._update_time_column, ['value'])
        self.generate_plots_button.on_click(self.generate_plots)

        self.corpus_loader.register_event_callback("build", self._update_corpus_list)
        self.corpus_loader.register_event_callback("rename", self._update_corpus_list)
        self.corpus_loader.register_event_callback("delete", self._update_corpus_list)

        panel.state.add_periodic_callback(self._update_corpus_list)

    def __panel__(self):
        return self.panel.servable()

    def _update_corpus_list(self, *_):
        self.log("Updated corpus list", logging.DEBUG)
        try:
            corpus_options: dict[str, DataFrameCorpus] = self.corpus_loader.get_corpora()
            if self.corpus_selector.options != corpus_options:
                self.corpus_selector.options = corpus_options
                if len(corpus_options):
                    self.corpus_selector.value = list(corpus_options.values())[-1]
        except Exception as e:
            self.log(str(traceback.format_exc()), logging.DEBUG)

    def _update_selected_corpus(self, *_):
        self.log("Updated selected corpus", logging.DEBUG)
        try:
            corpus: Optional[DataFrameCorpus] = self.corpus_selector.value
            if corpus is None:
                self.time_col_selector.value = None
                self.included_meta_selector.value = None
            else:
                meta_list: list[str] = corpus.metas
                selectable_list: list[str] = meta_list + [corpus._COL_DOC]
                if self.included_meta_selector.options != selectable_list:
                    self.included_meta_selector.options = selectable_list
                    self.included_meta_selector.value = selectable_list[0]
                datetime_metas: list[str] = [col for col in meta_list if is_datetime64_any_dtype(corpus.get_meta(col))]
                if self.time_col_selector.options != datetime_metas:
                    self.time_col_selector.options = datetime_metas
                    if len(datetime_metas):
                        self.time_col_selector.value = datetime_metas[0]
        except Exception as e:
            self.log(str(traceback.format_exc()), logging.DEBUG)

    def _update_time_column(self, *_):
        self.log("Updated time column", logging.DEBUG)
        try:
            corpus: Optional[DataFrameCorpus] = self.corpus_selector.value
            time_col: Optional[str] = self.time_col_selector.value
            if (corpus is None) or (time_col is None) or (time_col not in corpus.metas):
                self.date_range_picker.value = None
            else:
                date_series: Series = corpus.get_meta(time_col)
                self.date_range_picker.start = date_series.min()
                self.date_range_picker.end = date_series.max()
                self.date_range_picker.value = (self.date_range_picker.start, self.date_range_picker.end)
        except Exception as e:
            self.log(str(traceback.format_exc()), logging.DEBUG)

    def generate_plots(self, *_):
        try:
            if (self.corpus_selector.value is None) or (self.time_col_selector.value is None):
                return

            corpus: DataFrameCorpus = self.corpus_selector.value
            plot_df: DataFrame = corpus.to_dataframe()
            time_col: str = self.time_col_selector.value
            meta_col: str = self.included_meta_selector.value

            start_date, end_date = self.date_range_picker.value
            mask = (plot_df[time_col] >= start_date) & (plot_df[time_col] <= end_date)
            filtered_df = plot_df.loc[mask]

            plots = [
                self.create_raw_frequency_plot(filtered_df, time_col),
                self.create_meta_frequency_plot(filtered_df, time_col, meta_col)
            ]

            self.plots.objects = plots
        except Exception as e:
            self.log(str(traceback.format_exc()), logging.DEBUG)

    def create_raw_frequency_plot(self, plot_df: DataFrame, time_col: str) -> Plotly:
        self.log(f"create_raw_frequency_plot method: Plot_df: {plot_df.shape}, time_col: {time_col}", logging.DEBUG)

        date_grouping_periods = self.date_group_periods.value
        date_group_unit = self.date_group_unit_selector.value
        frequency: str = str(date_grouping_periods) + date_group_unit
        count_col_name: str = 'Document count'
        grouped_df = plot_df.groupby([Grouper(key=time_col, freq=frequency)]).size().reset_index(name=count_col_name)

        date_group_readable = CorpusVisualiser.TIME_PERIOD_INVERSE_GROUPINGS[date_group_unit]
        fig = px.line(grouped_df, x=time_col, y=count_col_name,
                      title=f"Document count by {date_group_readable} intervals")
        fig.update_traces(mode="lines+markers", marker=dict(size=10), line=dict(width=4))

        return Plotly(fig)

    def create_meta_frequency_plot(self, plot_df: DataFrame, time_col: str, meta_col: str) -> Plotly:
        """
        Creates a line plot of time by frequency within the specified meta column
        """
        self.log(f"create_meta_frequency_plot method: Plot_df: {plot_df.shape}, time_col: {time_col}, meta_col: {meta_col}", logging.DEBUG)

        date_grouping_periods = self.date_group_periods.value
        date_group_unit = self.date_group_unit_selector.value
        frequency: str = str(date_grouping_periods) + date_group_unit
        count_col_name: str = f'{meta_col} frequency'
        grouped_df = plot_df.groupby([Grouper(key=time_col, freq=frequency), meta_col]).size().reset_index(name=count_col_name)

        date_group_readable = CorpusVisualiser.TIME_PERIOD_INVERSE_GROUPINGS[date_group_unit]
        fig = px.line(grouped_df, x=time_col, y=count_col_name, color=meta_col, title=f"{meta_col} frequency breakdown by {date_group_readable} intervals")
        fig.update_traces(mode="lines+markers", marker=dict(size=10), line=dict(width=4))

        return Plotly(fig)
