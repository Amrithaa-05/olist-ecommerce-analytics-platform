# E-Commerce Supply Chain & Customer Analytics Platform

An end-to-end e-commerce analytics platform built using the Olist Brazilian E-Commerce dataset. The project combines data engineering, SQL analytics, machine learning, business intelligence, REST APIs, and a local GenAI assistant into a single application.

## Project Overview

The platform analyzes e-commerce orders, customers, products, sellers, payments, reviews, and delivery performance.

It provides:

- Data cleaning and ETL using Python
- Relational data storage and analytics using MySQL
- SQL-based business analysis
- RFM customer segmentation
- Delivery-delay prediction using XGBoost
- Power BI dashboards
- FastAPI backend APIs
- Streamlit interactive frontend
- Semantic intent routing for AI questions
- RAG-based project knowledge assistant
- Local Qwen3 LLM using Ollama
- Application-level response guardrails

## Architecture

```text
                    OLIST DATASET
                         |
                         v
              Python ETL + Validation
                         |
                         v
                      MySQL
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
       SQL/RFM        XGBoost          RAG
          |              |              |
          +--------------+--------------+
                         |
                         v
                      FastAPI
                         |
                         v
                     Streamlit
                         |
                         v
              Interactive AI Platform
                         |
                      Power BI