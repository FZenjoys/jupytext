import re
from nbformat.v4.nbbase import new_notebook, new_markdown_cell, new_code_cell
from jupytext.compare import compare, compare_notebooks
import jupytext
from .utils import skip_if_dict_is_not_ordered


@skip_if_dict_is_not_ordered
def test_read_mostly_py_rmd_file(rmd="""---
title: Simple file
---

```{python, echo=TRUE}
import numpy as np
x = np.arange(0, 2*math.pi, eps)
```

```{python, echo=TRUE}
x = np.arange(0,1,eps)
y = np.abs(x)-.5
```

```{r}
ls()
```

```{r, results="asis", magic_args="-i x"}
cat(stringi::stri_rand_lipsum(3), sep='\n\n')
```
"""):
    nb = jupytext.reads(rmd, 'Rmd')
    compare(nb.cells, [{'cell_type': 'raw',
                        'source': '---\ntitle: Simple file\n---',
                        'metadata': {}},
                       {'cell_type': 'code',
                        'metadata': {'echo': True},
                        'execution_count': None,
                        'source': 'import numpy as np\n'
                                  'x = np.arange(0, 2*math.pi, eps)',
                        'outputs': []},
                       {'cell_type': 'code',
                        'metadata': {'echo': True},
                        'execution_count': None,
                        'source': 'x = np.arange(0,1,eps)\ny = np.abs(x)-.5',
                        'outputs': []},
                       {'cell_type': 'code',
                        'metadata': {},
                        'execution_count': None,
                        'source': '%%R\nls()',
                        'outputs': []},
                       {'cell_type': 'code',
                        'metadata': {'results': 'asis'},
                        'execution_count': None,
                        'source': "%%R -i x\ncat(stringi::"
                                  "stri_rand_lipsum(3), sep='\n\n')",
                        'outputs': []}])

    rmd2 = jupytext.writes(nb, 'Rmd')
    rmd2 = re.sub(r'```{r ', '```{r, ', rmd2)
    rmd2 = re.sub(r'```{python ', '```{python, ', rmd2)
    compare(rmd2, rmd)


def test_markdown_cell_with_code_works(nb=new_notebook(cells=[
    new_markdown_cell("""```python
1 + 1
```""")])):
    text = jupytext.writes(nb, 'Rmd')
    nb2 = jupytext.reads(text, 'Rmd')
    compare_notebooks(nb2, nb)


def test_two_markdown_cell_with_code_works(nb=new_notebook(cells=[
    new_markdown_cell("""```python
1 + 1
```"""),
    new_markdown_cell("""```python
2 + 2
```""")
])):
    text = jupytext.writes(nb, 'Rmd')
    nb2 = jupytext.reads(text, 'Rmd')
    compare_notebooks(nb2, nb)


def test_tags_in_rmd(rmd='''---
jupyter:
  jupytext:
    text_representation:
      extension: .Rmd
      format_name: rmarkdown
      format_version: '1.1'
      jupytext_version: 1.2.3
---

```{python tags=c("parameters")}
p = 1
```
''', nb=new_notebook(cells=[new_code_cell('p = 1', metadata={'tags': ['parameters']})])):
    nb2 = jupytext.reads(rmd, 'Rmd')
    compare_notebooks(nb2, nb)


def round_trip_cell_metadata(cell_metadata):
    nb = new_notebook(metadata={'jupytext': {'main_language': 'python'}},
                      cells=[new_code_cell('1 + 1', metadata=cell_metadata)])
    text = jupytext.writes(nb, 'Rmd')
    nb2 = jupytext.reads(text, 'Rmd')
    compare_notebooks(nb2, nb)


def test_comma_in_metadata(cell_metadata={'a': 'b, c'}):
    round_trip_cell_metadata(cell_metadata)


def test_dict_in_metadata(cell_metadata={'a': {'b': 'c'}}):
    round_trip_cell_metadata(cell_metadata)


def test_list_in_metadata(cell_metadata={'d': ['e']}):
    round_trip_cell_metadata(cell_metadata)
