# Analytics & Dashboard Architecture

The Operations Dashboard provides real-time visibility into the health and utilization of the tenant's knowledge base and AI interactions.

## Data Flow

```mermaid
graph TD
    Client[Dashboard Frontend] --> |GET /api/v1/dashboard/*| Router[Dashboard Router]
    
    Router --> Service[Analytics Service]
    
    Service --> |SQL Aggregation| SQLite[(SQLite Metadata DB)]
    
    SQLite --> |COUNT, SUM, GROUP BY| Aggregation[Metric Aggregations]
    
    Aggregation --> Metrics[Data Points: Storage, Users, AI Tokens]
    
    Metrics --> Alerts[Alert Engine: Threshold Breaches]
    
    Metrics --> Response[API Response]
    Alerts --> Response
    
    Response --> Client
```

## Optimization Strategy
Instead of loading ORM models into Python memory and counting them, the `DashboardService` pushes all aggregation logic (`SUM`, `COUNT`, `AVG`) down into the SQLite query execution planner. This ensures that analytical queries execute in milliseconds, even across thousands of records, minimizing the impact on transactional workloads.
