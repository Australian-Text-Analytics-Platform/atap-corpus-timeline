# atap_corpus_timeline Documentation

---

## Docs

### atap_corpus_timeline.CorpusTimeline

Public interface for the CorpusTimeline module. A CorpusTimeline object can be used as a Panel component, i.e. will render in a Panel GUI

Can be imported using:

```python
from atap_corpus_timeline import CorpusTimeline
```

---

### CorpusLoader.\_\_init\_\_

CorpusLoader constructor

Params
- corpus_loader: Optional\[CorpusLoader\] - The CorpusLoader that the timeline will be attached to. If None, a default CorpusLoader will be created with no optional features. None by Default.
- run_logger: bool - If True, a log will be kept in the atap_corpus_loader directory. False by default
- params: Any – passed onto the panel.viewable.Viewer super-class

Example

```python
corpus_timeline = CorpusTimeline()
```

---

### CorpusTimeline.servable

Inherited from panel.viewable.Viewer. Call CorpusTimeline.servable() in a Jupyter notebook context to display the CorpusLoader widget.

Example

```python
corpus_timeline = CorpusTimeline()
corpus_timeline.servable()
```

### CorpusTimeline.get_corpus_loader

Returns the CorpusLoader object used by the CorpusTimeline to build and load the corpus. The CorpusLoader panel is displayed with the CorpusTimeline embedded as a tab.

Returns: CorpusLoader - the CorpusLoader object in which the CorpusTimeline is embedded.

Example

```python
corpus_timeline = CorpusTimeline()
loader = corpus_timeline.get_corpus_loader()
```

---

### CorpusTimeline.get_mutable_corpora

Returns the corpora object that contains the loaded corpus objects.
This allows adding to the corpora from outside the CorpusTimeline as the object returned is mutable, not a copy.
The Corpora object has a unique name constraint, meaning a corpus object cannot be added to the corpora if another corpus with the same name is already present. The same constraint applies to the rename method of corpus objects added to the corpora.

Returns: TCorpora - the mutable corpora object that contains the loaded corpus objects

Example

```python
corpus_timeline = CorpusTimeline()
corpora_object = corpus_timeline.get_mutable_corpora()
corpus = corpora_object.get("example")
```


## Example usage

The following snippet could be used as a cell in a Jupyter notebook. Each time the user builds a corpus, the corpus will be piped through the provided spaCy Language.

```python
import panel as pn
pn.extension("plotly")

from atap_corpus_timeline import CorpusTimeline
from atap_corpus_loader import CorpusLoader

loader = CorpusLoader(root_directory='corpus_data', include_meta_loader=True, run_logger=True)
corpus_timeline: CorpusTimeline = CorpusTimeline(corpus_loader=loader, run_logger=True)
corpus_timeline.servable()
```

