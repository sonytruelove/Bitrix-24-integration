from pydantic import BaseModel, EmailStr, Field


class LeadIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    phone: str = Field(min_length=5, max_length=32)
    email: EmailStr | None = None
    comment: str | None = None
    source: str = "WEBSITE"


class LeadOut(BaseModel):
    bitrix_id: int


class LeadStatus(BaseModel):
    id: int
    title: str
    status: str
    name: str | None = None
    phone: str | None = None
    email: str | None = None
