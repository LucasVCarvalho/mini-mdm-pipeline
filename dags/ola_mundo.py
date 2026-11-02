from datetime import datetime

from airflow.sdk import dag, task


@dag(
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["mini-mdm"],
)
def ola_mundo():
    @task
    def dizer_ola():
        print("Olá, pipeline de MDM!")

    dizer_ola()


ola_mundo()