"""Export notebook cells as text"""

import re
from copy import copy
from .languages import cell_language
from .cells import code_to_cell
from .cell_metadata import filter_metadata, is_active, \
    metadata_to_rmd_options, metadata_to_json_options
from .magics import escape_magic


def cell_source(cell):
    """
    Return the source of the current cell, as an array of lines
    :param cell:
    :return:
    """
    source = cell.source
    if source == '':
        return ['']
    if source.endswith('\n'):
        return source.splitlines() + ['']
    return source.splitlines()


def code_to_rmd(source, metadata, language):
    """
    Represent a code cell with given source and metadata as a rmd cell
    :param source:
    :param metadata:
    :param language:
    :return:
    """
    lines = []
    if not is_active('Rmd', metadata):
        metadata['eval'] = False
    options = metadata_to_rmd_options(language, metadata)
    lines.append(u'```{{{}}}'.format(options))
    lines.extend(source)
    lines.append(u'```')
    return lines


def code_to_r(source, metadata):
    """
    Represent a code cell with given source and metadata as a R cell
    :param source:
    :param metadata:
    :return:
    """
    lines = []
    if not is_active('R', metadata):
        metadata['eval'] = False
    options = metadata_to_rmd_options(None, metadata)
    if options:
        lines.append(u'#+ {}'.format(options))
    lines.extend(source)
    return lines


def code_to_py(source, metadata, padlines):
    """
    Represent a code cell with given source and metadata as a python cell
    """
    lines = []
    if not metadata:
        return source

    endofcell = metadata['endofcell']
    if endofcell == '-':
        del metadata['endofcell']
    options = metadata_to_json_options(metadata)
    lines.append('# + {}'.format(options))
    lines.extend(source)
    lines.extend([''] * padlines)
    lines.append('# {}'.format(endofcell))
    return lines


def py_endofcell_marker(source):
    """Issues #31 #38:  does the cell contain a blank line? In that case
    we add an end-of-cell marker"""
    endofcell = '-'
    while True:
        endofcell_re = re.compile(r'^#( )' + endofcell + r'\s*$')
        if list(filter(endofcell_re.match, source)):
            endofcell = endofcell + '-'
        else:
            return endofcell


class CellExporter():
    """A class that represent a notebook cell as text"""
    def __init__(self, cell, default_language, ext):
        self.ext = ext
        self.cell_type = cell.cell_type
        self.source = cell_source(cell)
        self.metadata = filter_metadata(cell.metadata)
        self.language = cell_language(self.source) or default_language

        # how many blank lines before end of cell marker
        self.padlines = cell.metadata.get('padlines', 0)

        # how many blank lines before next cell
        self.skiplines = cell.metadata.get('skiplines', 1)

        # for compatibility with v0.5.4 and lower (to be removed)
        if 'skipline' in cell.metadata:
            self.skiplines += 1
        if 'noskipline' in cell.metadata:
            self.skiplines -= 1

        if cell.cell_type == 'raw' and 'active' not in self.metadata:
            self.metadata['active'] = ''

    def is_code(self):
        """Is this cell a code cell?"""
        if self.cell_type == 'code':
            return True
        if self.cell_type == 'raw' and 'active' in self.metadata:
            return True
        return False

    def cell_to_text(self):
        """Return the text representation for the cell"""
        if self.is_code():
            return self.code_to_text()

        return self.markdown_escape(self.source)

    def markdown_escape(self, source):
        """Escape the given source, for a markdown cell"""
        if self.ext == '.Rmd':
            return source
        if self.ext == '.R':
            return ["#' " + line if line else "#'" for line in source]
        return ['# ' + line if line else '#' for line in source]

    def explicit_start_marker(self, source):
        """Does the python representation of this cell requires an explicit
        start of cell marker?"""
        if self.metadata:
            return True
        if all([line.startswith('#') for line in self.source]):
            return True
        if code_to_cell(self, source, False)[1] != len(source):
            return True

        return False

    def code_to_text(self):
        """Return the text representation of a code cell"""
        active = is_active(self.ext, self.metadata)
        if self.ext in ['.R', '.py']:
            if active and self.language != (
                    'R' if self.ext == '.R' else 'python'):
                active = False
                self.metadata['active'] = 'ipynb'
                self.metadata['language'] = self.language

        source = copy(self.source)
        if active:
            escape_magic(source, self.language)

        if self.ext == '.Rmd':
            return code_to_rmd(source, self.metadata, self.language)

        if not active:
            source = ['# ' + line if line else '#' for line in source]

        if self.ext == '.R':
            return code_to_r(source, self.metadata)

        # py
        if self.explicit_start_marker(source):
            self.metadata['endofcell'] = py_endofcell_marker(source)

        return code_to_py(source, self.metadata, self.padlines)
