#!/bin/bash

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLS_DIR="$PROJECT_ROOT/tools"
GENERATOR_DIR="$TOOLS_DIR/Grammar-Mutator"

# 1. prerequisites
sudo apt install valgrind uuid-dev default-jre 
wget https://www.antlr.org/download/antlr-4.8-complete.jar
sudo cp -f antlr-4.8-complete.jar /usr/local/lib
rm antlr-4.8-complete.jar

# 2. AFL++ libraries build
# the grammar mutator is based on the latest custom mutator APIs in AFL++
cd "$TOOLS_DIR"
git clone https://github.com/AFLplusplus/AFLplusplus.git
cd AFLplusplus
make

# 3. Grammar mutator build
cd "$GENERATOR_DIR"
if [ ! -f "grammars/bash.json" ]; then
    mkdir -p grammars
    cp ${PROJECT_ROOT}/docs/bash_grammar.json grammars/bash.json
fi
make GRAMMAR_FILE=grammars/bash.json

# 4. dynamic link the generator
cd "$TOOLS_DIR"
ln -s "$GENERATOR_DIR/grammar_generator-bash" grammar_generator-bash

# bin finally path: tools/grammar_generator-bash