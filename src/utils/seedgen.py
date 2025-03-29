from pathlib import Path

def generate_seed_scripts(seed_dir: Path, seed_count: int = 10, seed_depth: int = 100) -> None:
    """
    Generates a random seed for use in the application.
    """
    # call command: ./generate_mutator-bash.sh -o <seed_dir> <seed_count> <seed_depth> 
    # it will gen <seed_dir>/seeds/{0..seed_count} and <seed_dir>/trees/{0..seed_count}
    # the seeds are bash scripts and the trees are the corresponding parse trees
    # TODO: 
    # - move the file from subdir <seed_dir>/seeds to <seed_dir>
    # - remove the subdir seeds and trees
    pass