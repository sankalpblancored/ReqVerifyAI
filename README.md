# ReqVerify AI

## Intelligent Software Requirement Consistency and Workflow Verification System

ReqVerify AI is a software requirement analysis and workflow verification system. It analyzes software requirements, extracts functional requirements and workflow information, represents the workflow as a Finite State Machine (FSM), and performs structural and sequence-based verification.

## Features

- Software requirement input through text or document upload
- Functional requirement extraction
- Requirement-to-FSM traceability
- Workflow extraction
- Finite State Machine generation
- Reachability analysis
- Unreachable-state detection
- Dead-end-state detection
- Rule-based requirement consistency checking
- Manual sequence validation
- Automatic sequence validation
- Explainable verification recommendations
- FSM visualization
- Experimental validation
- State and transition coverage
- Controlled verification test mode
- Verification summary and report generation

## Technology Stack

- Python
- Streamlit
- NetworkX
- Matplotlib
- pypdf

## Project Structure

```text
ReqVerifyAI/
│
├── app.py
├── consistency.py
├── fsm.py
├── parser.py
├── requirements.py
│
├── test_fsm.py
├── test_integration.py
├── test_parser.py
│
├── requirements.txt
├── README.md
└── diagrams/