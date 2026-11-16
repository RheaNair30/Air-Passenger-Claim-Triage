
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class ClaimEnum(str, Enum):
    """Shared categorical values used by the claim contract."""

    pass


class BookingContactProvided(str, Enum):
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"


class FlightSector(str, Enum):
    DOMESTIC = "domestic"
    INTERNATIONAL = "international"
    UNKNOWN = "unknown"


class DisruptionType(str, Enum):
    DENIED_BOARDING = "denied_boarding"
    CANCELLATION = "cancellation"
    DELAY = "delay"
    DOWNGRADING = "downgrading"
    UNSPECIFIED = "unspecified"


class DisruptionCause(str, Enum):
    WEATHER = "weather"
    ATC = "atc"
    TECHNICAL = "technical"
    SECURITY = "security"
    STRIKE = "strike"
    CREW = "crew"
    OTHER = "other"
    UNKNOWN = "unknown"


class TravelClass(str, Enum):
    FIRST = "first"
    BUSINESS = "business"
    PREMIUM_ECONOMY = "premium_economy"
    ECONOMY = "economy"


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class Passenger(StrictModel):
    name: str = Field(min_length=1, max_length=100)
    email: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=100)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        if value is not None:
            import re
            if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
                raise ValueError("Invalid email format")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value):
        if value is not None:
            import re
            if not re.fullmatch(r"\+?\d+", value):
                raise ValueError("Phone must contain digits with an optional leading +")
        return value


class Flight(StrictModel):
    airline_iata: str = Field(pattern=r"^[A-Za-z]{2}$")
    number: str = Field(pattern=r"^\d{1,4}[A-Za-z]?$")
    origin: str = Field(pattern=r"^[A-Za-z]{3}$")
    destination: str = Field(pattern=r"^[A-Za-z]{3}$")

    scheduled_departure: datetime
    scheduled_arrival: Optional[datetime] = None

    sector: FlightSector = FlightSector.UNKNOWN
    block_time_minutes_stated: Optional[int] = Field(
        default=None, gt=0
    )

    @field_validator("airline_iata", "origin", "destination")
    @classmethod
    def uppercase_codes(cls, value):
        return value.upper()

    @field_validator("scheduled_departure", "scheduled_arrival")
    @classmethod
    def require_timezone(cls, value):
        if value is not None and (
            value.tzinfo is None or value.utcoffset() is None
        ):
            raise ValueError("Datetime must include a timezone")
        return value


class Disruption(StrictModel):
    claimed_type: DisruptionType = DisruptionType.UNSPECIFIED

    notified_at: Optional[datetime] = None
    notice_hours_before_departure: Optional[float] = Field(
        default=None, ge=0
    )

    reported_at_airport: Optional[bool] = None

    alternate_flight_offered: Optional[bool] = None
    alternate_flight_accepted: Optional[bool] = None
    alternate_departure: Optional[datetime] = None

    delay_minutes: Optional[int] = Field(default=None, ge=0)

    stated_cause: DisruptionCause = DisruptionCause.UNKNOWN

    booked_class: Optional[TravelClass] = None
    travelled_class: Optional[TravelClass] = None

    @field_validator("notified_at", "alternate_departure")
    @classmethod
    def require_timezone(cls, value):
        if value is not None and (
            value.tzinfo is None or value.utcoffset() is None
        ):
            raise ValueError("Datetime must include a timezone")
        return value


class Fare(StrictModel):
    basic_fare_inr: Optional[Decimal] = Field(default=None, ge=0)
    fuel_charge_inr: Optional[Decimal] = Field(default=None, ge=0)
    ticket_total_inr: Optional[Decimal] = Field(default=None, ge=0)


class ClaimInput(StrictModel):
    client_reference: Optional[str] = Field(default=None, max_length=100)
    follow_up_of: Optional[str] = Field(default=None, max_length=100)

    narrative: str = Field(min_length=1, max_length=2000)

    passenger: Passenger
    booking_contact_provided: BookingContactProvided = (
        BookingContactProvided.UNKNOWN
    )

    pnr: str = Field(pattern=r"^[A-Za-z0-9]{6}$")

    flight: Flight
    disruption: Disruption = Field(default_factory=Disruption)
    fare: Fare = Field(default_factory=Fare)

    @field_validator("pnr")
    @classmethod
    def uppercase_pnr(cls, value):
        return value.upper()

    @model_validator(mode="after")
    def validate_business_integrity(self):
        # B1: A journey must have different origin and destination.
        if self.flight.origin == self.flight.destination:
            raise ValueError(
                "B1: Flight origin and destination must differ"
            )

        # B2: Scheduled arrival must follow scheduled departure.
        arrival = self.flight.scheduled_arrival
        departure = self.flight.scheduled_departure

        if arrival is not None and arrival <= departure:
            raise ValueError(
                "B2: Scheduled arrival must be after scheduled departure"
            )

        # B3: Alternate-flight details require an offered alternate.
        offered = self.disruption.alternate_flight_offered

        if offered is not True:
            if (
                self.disruption.alternate_flight_accepted is not None
                or self.disruption.alternate_departure is not None
            ):
                raise ValueError(
                    "B3: Alternate-flight acceptance and departure "
                    "require an alternate flight to have been offered"
                )

        # B4: Total ticket fare must cover basic fare plus fuel charge.
        basic = self.fare.basic_fare_inr
        fuel = self.fare.fuel_charge_inr
        total = self.fare.ticket_total_inr

        if basic is not None and fuel is not None and total is not None:
            if total < basic + fuel:
                raise ValueError(
                    "B4: Ticket total cannot be below basic fare "
                    "plus fuel charge"
                )

        return self