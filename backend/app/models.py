from pydantic import BaseModel

class JobInput(BaseModel):
    job_text: str