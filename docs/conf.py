# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Bambu Labs Timelapse Downloader'
copyright = '2024, Stephen Golub'
author = 'Stephen Golub'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "autoapi.extension",
    "autodocsumm",
    "myst_parser",
    "sphinx_design",
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinxcontrib.runcmd",
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']

dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../aoc'))
autoapi_dirs = [dir_path]
#  autoapi_generate_api_docs = False
autoapi_template_dir = "_templates"
autoapi_python_class_content = "both"
autoapi_options = [
    'members',
    'undoc-members',
    'private-members',
    'show-inheritance',
    'special-members',
    'imported-members',
]
autodoc_typehints = "description"
autodoc_typehints_format = "short"

add_module_names = False

