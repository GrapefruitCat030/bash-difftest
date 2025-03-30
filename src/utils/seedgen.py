from pathlib import Path
import shutil
import subprocess

def generate_seed_scripts(seed_dir: Path, seed_count: int = 10, seed_depth: int = 100) -> None:
    """
    Generates a random bash scripts seeds.
    """
    seed_dir.mkdir(parents=True, exist_ok=True)
    subdir_seeds = seed_dir / "seeds"
    subdir_trees = seed_dir / "trees"
    # generate seeds 
    try:
        subprocess.run(
            ["tools/grammar_generator-bash", str(seed_count), str(seed_depth), str(subdir_seeds), str(subdir_trees)], # TODO: hardcode, to be changed
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error while generating seeds: {e}")
        return

    # move files from <seed_dir>/seeds to <seed_dir>
    if subdir_seeds.exists() and subdir_seeds.is_dir():
        for seed_file in subdir_seeds.iterdir():
            if seed_file.is_file():
                shutil.move(str(seed_file), str(seed_dir))

    # remove the <seed_dir>/seeds and <seed_dir>/trees
    for subdir in [subdir_seeds, subdir_trees]:
        if subdir.exists() and subdir.is_dir():
            shutil.rmtree(subdir)
    
    # now remains only the <seed_dir> with the generated seeds