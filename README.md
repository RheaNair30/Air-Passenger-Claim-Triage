# Air-Passenger-Claim-Triage
Multi-agent air passenger compensation claim triage service using DGCA regulations and airline conditions of carriage.

## Project Overview

The system accepts passenger claims related to flight disruptions, validates submitted information, identifies relevant regulatory provisions, and generates evidence-grounded recommendations.

Each recommendation includes supporting clause references and is routed for further action where necessary.

**The system provides decision support only. It does not authorize or process compensation payments.**

## Objectives

- Validate incoming passenger claims.
- Classify flight disruptions and extract relevant details.
- Retrieve applicable DGCA and airline provisions.
- Evaluate entitlement using supporting evidence and clause citations.
- Route claims for resolution, additional evidence, or escalation.
- Maintain traceability through logs, metrics, and evaluation.

## Planned Technology

- **Backend:** Python, FastAPI
- **Agent orchestration:** LangGraph
- **LLM framework:** LangChain
- **Vector database:** Chroma
- **Database:** PostgreSQL
- **Queue and background processing:** Redis and Arq
- **Deployment:** Docker Compose

*These are planned technologies; implementation details may evolve.*

## Regulatory Sources

- DGCA Civil Aviation Requirements, Section 3, Series M, Part IV, Revision 4.
- Airline Conditions of Carriage (subject to confirmation of the approved airline source).

## Project Status

Pre-implementation planning and architecture design completed. Development, integration, testing, and evaluation are pending.

## Disclaimer

This project is an academic decision-support prototype. Its recommendations are not legally binding and do not replace decisions by the airline or relevant regulatory authorities.
