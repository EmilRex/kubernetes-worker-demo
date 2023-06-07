from prefect import flow, task, get_run_logger, tags
from prefect.deployments import run_deployment

NAMES = [
    "Marvin",
    "Ford",
    "Arthur",
    "Trillian",
    "Zaphod",
]


@flow
def hello(name: str = "Marvin"):
    logger = get_run_logger()
    logger.info(f"Hello, {name}!")


@task
def say_hello_parallel(name: str):
    run_deployment("hello/default", parameters={"name": name})


@flow
def hello_parallel(names: list = NAMES):
    for name in names:
        say_hello_parallel.submit(name)


if __name__ == "__main__":
    with tags("local"):
        hello()
