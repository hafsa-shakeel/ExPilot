<img width="872" height="540" alt="image" src="https://github.com/user-attachments/assets/a41bb56e-60df-4ec8-8014-4c3ccb6c2c4c" /># ExPilot

Welcome to the ExPilot repository, built using Flask (Python) for the backend and React for the frontend!
This project is designed to help businesses with multiple locations manage branches, budgets, utility bills, alerts, and financial reporting efficiently.

## Table of Contents

- Problem Solved / Motivation
- Introduction
- Features
- Installation Instructions
- Usage Instructions
- Database Schema
- Technologies Used
- Contributing

## Motivation

Managing utilities and budgets across multiple branches can be time-consuming, error-prone, and lacking real-time visibility.
Businesses face challenges like:
- Manual tracking of budgets and expenses.
- No automatic alerts for overspending.
- Difficulty comparing performance between branches.
- Lack of centralized access for multiple roles.

ExPilot addresses these problems by:
- Centralizing branch, budget, and utility bill data.
- Automating budget overrun and threshold alerts.
- Providing role-based dashboards for Business Owner (Admin), Managers, and SuperAdmin.
- Enabling data-driven decisions with branch performance reports.

## Introduction
The ExPilot is a web-based application for multi-location businesses to streamline branch operations, budget allocation, expense tracking, and alert management.
The system supports role-based dashboards for Business Owners, Branch Managers, and SuperAdmins to ensure secure and structured access.

## Features
1) Role-Based Dashboards: Separate views for Admin, Manager, and SuperAdmin users.
2) Branch Management: Add, update, deactivate/reactivate branches, and assign branch managers.
3) Budget Management: Allocate, update, and track monthly/yearly budgets with history.
4) Expense Management: Upload utility bills with media attachments and detailed tracking.
5) Real-Time Alerts: Auto-generate alerts for budget overruns or threshold breaches.
6) Branch Performance Comparison: Compare budgets, expenses, and profit/loss between branches.
7) Reports: Profit/Loss summaries and branch-wise expense analysis.
8) Authentication & Authorization: Secure login with session handling.

## Installation Instructions
Prerequisites
- Backend: Python 3.10+, pip, Microsoft SQL Server (or SQL Server Express)
- Frontend: Node.js 18+, npm
- Common: GitHub account to clone this repo

## Backend Setup
**Note:** Before running the backend server, ensure SQL Server is installed and accessible. Update your `.env` file with database credentials.

#### 1. Clone the repository:
```bash
git clone https://github.com/hafsa-shakeel/ExPilot.git
cd ExPilot
```

#### 2. Create and Activate Virtual Environment:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Mac/Linux
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
pip install flask flask flask-cors flask-session bcrypt python-dotenv pyodbc
```

#### 4. Run Backend
```bash
python run.py
```
Backend will run on http://localhost:5000

## Frontend Setup
```bash
cd frontend_umd
npm install
npm start
```
Frontend will run on http://localhost:3000

## Usage
### Admin Actions:
- Register & manage branches.
- Allocate & update budgets.
- View all branch expenses & performance.
- Compare branches.
- Manage business profile.

### Branch Manager Actions:
- View assigned branch dashboard.
- Upload utility bills.
- Track branch budget & expenses.
- View profit/loss summaries.

## Database Schema








