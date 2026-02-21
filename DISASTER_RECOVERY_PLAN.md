# Disaster Recovery (DR) Plan for The Intaker

This document outlines the disaster recovery plan for The Intaker project to ensure business continuity and data availability in the event of a disaster.

## 1. Introduction

This DR plan details the strategies and procedures to recover critical services and data in the event of a partial or complete outage of one or more Google Cloud regions.

## 2. Roles and Responsibilities

*   **DR Team Lead**: Responsible for overseeing the DR plan and execution.
*   **Engineering Team**: Responsible for implementing and testing the DR procedures.
*   **Communications Lead**: Responsible for internal and external communications during a DR event.

## 3. Recovery Objectives

*   **Recovery Time Objective (RTO)**: The target time to recover critical services after a disaster. **RTO: 1 hour**
*   **Recovery Point Objective (RPO)**: The maximum acceptable amount of data loss. **RPO: 5 minutes**

## 4. High Availability and DR Strategies

### 4.1. Compute (Cloud Run and Cloud Functions)

*   **High Availability**: The main application is deployed to two Google Cloud regions (`us-central1` and `us-east1`). A global external HTTPS load balancer distributes traffic between the two regions, automatically failing over if one region becomes unavailable.
*   **Disaster Recovery**: In the event of a full regional outage, the load balancer will automatically route all traffic to the healthy region. No manual intervention is required.

### 4.2. Data (Cloud Firestore, Cloud Storage, and Cloud KMS)

*   **Cloud Firestore**:
    *   **High Availability**: Firestore is deployed in a multi-region configuration (`nam5`), which provides automatic, synchronous replication across multiple regions.
    *   **Disaster Recovery**: Point-in-Time Recovery (PITR) is enabled, allowing for recovery to any point in the last 7 days with one-minute granularity. Daily backups are also taken and retained for 7 days.
*   **Cloud Storage**:
    *   **High Availability**: Patient documents are stored in a dual-region Cloud Storage bucket, providing automatic data redundancy across two regions.
    *   **Disaster Recovery**: Object versioning and a 7-day soft delete policy are enabled to protect against accidental data loss.
*   **Cloud KMS**:
    *   **High Availability**: Encryption keys are stored in a multi-regional KMS key ring, ensuring they are available even if a single region is down.

## 5. DR Testing and Orchestration

### 5.1. Testing Procedures

DR testing will be conducted quarterly to ensure the effectiveness of the plan. The following tests will be performed:

*   **Failover Test**: Simulate a regional outage by manually failing over the Cloud Run service to a single region. Verify that the application remains available and that the load balancer correctly routes traffic.
*   **Firestore Restore Test**: Restore a Firestore backup to a new project and verify the integrity of the data.
*   **Storage Restore Test**: Restore a deleted object from a Cloud Storage bucket using the soft delete feature and from a previous version using object versioning.

### 5.2. Orchestration

In the event of a disaster, the following steps will be taken:

1.  **Declare a Disaster**: The DR Team Lead will declare a disaster after confirming a sustained outage of a critical service.
2.  **Execute DR Plan**: The Engineering Team will execute the DR procedures as outlined in this document.
3.  **Communications**: The Communications Lead will provide regular updates to internal stakeholders and customers.
4.  **Post-Mortem**: After the disaster is resolved, a post-mortem will be conducted to identify areas for improvement in the DR plan.

## 6. Document Maintenance

This DR plan will be reviewed and updated annually, or after any significant changes to the system architecture.
