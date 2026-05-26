project = 'gemsparcl'
copyright = '2026, Johanna von Wachsmann'
author = 'Johanna von Wachsmann'
release = '1.0.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx_design',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'furo'
html_static_path = ['_static']

html_logo = '_static/logo.png'
html_title = 'gemsparcl'

html_theme_options = {
    'sidebar_hide_name': True,
    'light_css_variables': {
        'color-background-primary': '#faf9ff',
        'color-background-secondary': '#f2efff',
        'color-background-hover': '#e8e3ff',
        'color-background-hover--transparent': '#e8e3ff00',
        'color-brand-primary': '#7c5cbf',
        'color-brand-content': '#6b4fad',
    },
    'dark_css_variables': {
        'color-background-primary': '#1a1825',
        'color-background-secondary': '#211e30',
        'color-brand-primary': '#b49de0',
        'color-brand-content': '#c4aeee',
    },
}

# Napoleon — support for Google-style and NumPy-style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_use_rtype = True

# Autodoc
autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
autodoc_mock_imports = ['numpy', 'pandas']
autodoc_default_options = {
    'members': True,
    'undoc-members': False,
    'show-inheritance': True,
}

# Intersphinx — cross-links to external library docs
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'networkx': ('https://networkx.org/documentation/stable', None),
    'pandas': ('https://pandas.pydata.org/docs', None),
    'numpy': ('https://numpy.org/doc/stable', None),
}
