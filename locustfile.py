from locust import HttpUser, task, between


class MyApiUser(HttpUser):
    wait_time = between(0.1, 1)

    @task
    def get_team(self):
        self.client.get("/team/get?team_name=test")
