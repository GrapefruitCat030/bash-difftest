import os
import tree_sitter

# Initialize tree-sitter parser
def initialize_parser():
    tree_sitter_bash_path = os.path.join(os.getcwd(), 'tree-sitter-bash')
    tree_sitter.Language.build_library(
        'build/my-languages.so',
        [tree_sitter_bash_path]
    )
    BASH_LANGUAGE = tree_sitter.Language('build/my-languages.so', 'bash')
    parser = tree_sitter.Parser()
    parser.set_language(BASH_LANGUAGE)
    return parser