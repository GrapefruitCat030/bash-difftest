from .llm_util import read_file
from .llm_client import call_deepseek_api

def generate_transformer(posix_doc: str, target_shell: str, target_doc: str) -> str:
    template = read_file("docs/mutator_doc/template.txt")
    prompt = template.replace("{{posix_doc}}", posix_doc) \
                     .replace("{{target_shell}}", target_shell) \
                     .replace("{{target_doc}}", target_doc)
    return call_deepseek_api(prompt)


if __name__ == "__main__":
    # Read POSIX documentation
    posix_doc = read_file("docs/mutator_doc/posix/loop.txt")

    # Generate Bash transformer
    bash_doc = read_file("docs/mutator_doc/bash/loop.txt")
    bash_transformer = generate_transformer(posix_doc, "Bash", bash_doc)
    print("Bash Transformer:")
    print(bash_transformer)
    with open('output/bash_transformer_output.txt', 'w') as f:
        f.write("Bash Transformer:\n")
        f.write(str(bash_transformer) + "\n")

    # Generate Fish transformer
    fish_doc = read_file("docs/mutator_doc/fish/loop.txt")
    fish_transformer = generate_transformer(posix_doc, "Fish", fish_doc)
    print("\nFish Transformer:")
    print(fish_transformer)
    with open('output/fish_transformer_output.txt', 'w') as f:
        f.write("Fish Transformer:\n")
        f.write(str(fish_transformer) + "\n")

    # Generate Zsh transformer
    zsh_doc = read_file("docs/mutator_doc/zsh/loop.txt")
    zsh_transformer = generate_transformer(posix_doc, "Zsh", zsh_doc)
    print("\nZsh Transformer:")
    print(zsh_transformer)
    with open('output/zsh_transformer_output.txt', 'w') as f:
        f.write("Zsh Transformer:\n")
        f.write(str(zsh_transformer) + "\n")