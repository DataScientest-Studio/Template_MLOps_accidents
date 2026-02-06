# Phase 2-4 Tickets and Plan Updates

## Part 1: Comparison and Suggested Updates

### Status Discrepancies Between Jira and Plan Documents

**Phase 1 Status Updates Needed:**

1. **MLflow Integration (MRA2-13 / ML-2)**

- **Jira Status**: Done ✅
- **Plan Status**: Not Started ❌
- **Action**: Update `doc/Plan_Phase_01.md` to reflect completion (100%)

2. **Baseline Model Definition (MRA2-12 / ML-0)**

- **Jira Status**: Done ✅
- **Plan Status**: 70% Complete 🚧
- **Action**: Update plan to reflect 100% completion

3. **Model Evaluation (MRA2-16 / ML-3)**

- **Jira Status**: Done ✅
- **Plan Status**: 60% Complete 🚧
- **Action**: Verify DVC metrics format completion, update plan accordingly

4. **Multi-Model Training Pipeline (MRA2-20)**

- **Jira Status**: Done ✅ (Epic with all subtasks complete)
- **Plan Status**: Not explicitly tracked
- **Action**: Add to Phase 1 completion summary

### Suggested Ticket Updates

**MRA2-27: Microservices Architecture Design**

- **Current**: "still needed?" - To Do
- **Recommendation**: 
- If keeping microservices: Move to Phase 2, rename to "Microservices Architecture Design & Implementation"
- If not needed: Close as "Won't Do" with rationale (monolithic FastAPI + Streamlit sufficient for current scale)

**MRA2-19: Fetch Additional Raw Data**

- **Current**: In Progress
- **Recommendation**: Complete or defer to Phase 2 if not critical for Phase 1

**MRA2-11: Validation Pipeline**

- **Current**: In Progress
- **Recommendation**: Complete before Phase 1 closure

**MRA2-14: FastAPI Skeleton**

- **Current**: In Progress
- **Recommendation**: Complete before Phase 1 closure

**MRA2-17: Unit Test Implementation**

- **Current**: To Do
- **Recommendation**: Complete before Phase 1 closure

**MRA2-18: GitHub Actions CI**

- **Current**: To Do
- **Recommendation**: Complete before Phase 1 closure

---

## Part 2: Phase 2 Tickets (Microservices, Tracking & Versioning)

**Deadline: January 16th, 2026**

### Epic: MRA2-28 - Phase 2: Microservices, Tracking & Versioning

**Description**: Decompose application into microservices, enhance versioning, and complete tracking infrastructure.

**Subtasks**:

#### MRA2-29: Microservices Architecture Design

- **Type**: Task
- **Assignee**: Engineer C (with input from all)
- **Parent**: MRA2-28
- **Priority**: High
- **Description**: 
Design microservices architecture separating data, training, and API services. Define service boundaries, communication protocols, and orchestration strategy.

**Acceptance Criteria**:

- Architecture diagram documenting service boundaries
- API contracts defined between services
- Data flow diagrams for each microservice
- Decision on orchestration tool (Docker Compose, Kubernetes, or simple service mesh)
- Documented rationale for microservices vs monolithic approach
- Service dependency graph

#### MRA2-30: Data Service Microservice

- **Type**: Task
- **Assignee**: Engineer A
- **Parent**: MRA2-28
- **Priority**: High
- **Description**: 
Extract data ingestion and preprocessing into a standalone microservice with REST API endpoints.

**Acceptance Criteria**:

- FastAPI service for data operations (`src/services/data_service/`)
- Endpoints: `/data/import`, `/data/validate`, `/data/preprocess`
- Service runs in Docker container (`docker-compose.yml` service: `data-service`)
- Integration with DVC for data versioning
- Health check endpoint (`/health`)
- Error handling and logging
- Service can be called independently from training service

#### MRA2-31: Training Service Microservice

- **Type**: Task
- **Assignee**: Engineer B
- **Parent**: MRA2-28
- **Priority**: High
- **Description**: 
Extract model training into a standalone microservice with REST API endpoints for triggering training jobs.

**Acceptance Criteria**:

- FastAPI service for training operations (`src/services/training_service/`)
- Endpoints: `/training/train`, `/training/status/{job_id}`, `/training/models`
- Async job processing (background tasks)
- Integration with MLflow for experiment tracking
- Service runs in Docker container (`docker-compose.yml` service: `training-service`)
- Health check endpoint (`/health`)
- Job status tracking and retrieval
- Error handling and logging

#### MRA2-32: API Service Microservice (Inference)

- **Type**: Task
- **Assignee**: Engineer C
- **Parent**: MRA2-28
- **Priority**: High
- **Description**: 
Extract prediction API into a standalone microservice optimized for inference.

**Acceptance Criteria**:

- FastAPI service for predictions (`src/services/api_service/` or `src/api/`)
- Endpoints: `/predict`, `/health`, `/models/available`
- Model loading from MLflow registry or local filesystem
- Service runs in Docker container (`docker-compose.yml` service: `api-service`)
- Health check with model availability status
- Request/response logging
- Error handling and validation

#### MRA2-33: Service Orchestration Setup

- **Type**: Task
- **Assignee**: Engineer C
- **Parent**: MRA2-28
- **Priority**: Medium
- **Description**: 
Set up orchestration for microservices using Docker Compose (or Kubernetes if scaling required).

**Acceptance Criteria**:

- Updated `docker-compose.yml` with all microservices
- Service discovery and networking configured
- Health checks and restart policies
- Environment variable management for service communication
- Documentation for local development setup
- Service dependency ordering (data → training → api)

Enhanced DVC Data Versioning

- **Type**: Task
- **Assignee**: Engineer A
- **Parent**: MRA2-28
- **Priority**: Medium
- **Description**: 
Enhance DVC pipeline with comprehensive data versioning, including data lineage tracking.

**Acceptance Criteria**:

- DVC pipeline tracks all data transformations
- Data version tags and metadata
- Data lineage visualization (DVC DAG)
- Automated data versioning on pipeline runs
- Documentation of data versioning workflow
- Integration with Dagshub for remote storage

#### MRA2-35: MLflow Model Registry Enhancement

- **Type**: Task
- **Assignee**: Engineer B
- **Parent**: MRA2-28
- **Priority**: Medium
- **Description**: 
Enhance MLflow model registry with automated model promotion workflows and model comparison dashboards.

**Acceptance Criteria**:

- Automated model comparison reports
- Model promotion workflow automation (staging → production)
- Model performance tracking over time
- Integration with training service for automatic registration
- Model registry API endpoints for external access
- Documentation of model lifecycle management

#### MRA2-36: Inter-Service Communication

- **Type**: Task
- **Assignee**: Engineer C
- **Parent**: MRA2-28
- **Priority**: Medium
- **Description**: 
Implement communication patterns between microservices (REST APIs, message queues if needed).

**Acceptance Criteria**:

- REST API clients for inter-service communication
- Error handling and retry logic
- Service authentication/authorization (if needed)
- Request/response logging
- Timeout and circuit breaker patterns
- Documentation of service communication protocols

---

## Part 3: Phase 3 Tickets (Orchestration & Deployment)

**Deadline: January 29th, 2026**

### Epic: MRA2-37 - Phase 3: Orchestration & Deployment

**Description**: Finalize orchestration, implement CI/CD, optimize API, and prepare for scalability.

**Subtasks**:

#### MRA2-38: End-to-End Orchestration Finalization

- **Type**: Task
- **Assignee**: Engineer C (with support from all)
- **Parent**: MRA2-37
- **Priority**: High
- **Description**: 
Finalize end-to-end orchestration workflow from data ingestion to model serving.

**Acceptance Criteria**:

- Complete workflow: data import → preprocessing → training → model deployment → API serving
- Automated pipeline triggers (on data update, schedule, or manual)
- Pipeline status monitoring and notifications
- Error recovery and rollback mechanisms
- Pipeline execution logs and audit trail
- Documentation of orchestration workflow

#### MRA2-39: GitHub Actions CI Pipeline Enhancement

- **Type**: Task
- **Assignee**: Engineer C
- **Parent**: MRA2-37
- **Priority**: High
- **Description**: 
Enhance CI pipeline with comprehensive testing, linting, security scanning, and Docker image building.

**Acceptance Criteria**:

- Workflow: `.github/workflows/ci.yaml` with:
- Linting (black, flake8, isort)
- Type checking (mypy)
- Unit tests with coverage reporting (>70% threshold)
- Integration tests for microservices
- Docker image building and pushing to registry
- Security scanning (dependencies, Docker images)
- PR checks must pass before merge
- Coverage reports published as artifacts
- Badge in README showing CI status

#### MRA2-40: API Optimization and Performance

- **Type**: Task
- **Assignee**: Engineer C
- **Parent**: MRA2-37
- **Priority**: High
- **Description**: 
Optimize API service for production performance and scalability.

**Acceptance Criteria**:

- Response time < 100ms for predictions (p95)
- Request rate limiting implemented
- Caching strategy for model loading
- Async request handling
- Connection pooling
- Performance benchmarks documented
- Load testing results (handles X concurrent requests)

#### MRA2-41: API Security Implementation

- **Type**: Task
- **Assignee**: Engineer C
- **Parent**: MRA2-37
- **Priority**: High
- **Description**: 
Implement security measures for API endpoints.

**Acceptance Criteria**:

- API authentication (API keys or OAuth2)
- Input validation and sanitization
- Rate limiting per user/API key
- HTTPS/TLS configuration
- CORS configuration
- Security headers (X-Content-Type-Options, etc.)
- Security documentation

#### MRA2-42: Docker/Kubernetes Scalability Setup

- **Type**: Task
- **Assignee**: Engineer C
- **Parent**: MRA2-37
- **Priority**: Medium
- **Description**: 
Prepare infrastructure for horizontal scaling using Docker Swarm or Kubernetes.

**Acceptance Criteria**:

- Kubernetes manifests (or Docker Swarm configs) for all services
- Horizontal Pod Autoscaling (HPA) configuration
- Resource limits and requests defined
- Service mesh or load balancer configuration
- Documentation for deployment to Kubernetes
- Local Kubernetes setup (minikube/kind) for testing

#### MRA2-43: Production Deployment Documentation

- **Type**: Task
- **Assignee**: Engineer C
- **Parent**: MRA2-37
- **Priority**: Medium
- **Description**: 
Create comprehensive deployment documentation for production environments.

**Acceptance Criteria**:

- Deployment guide for cloud providers (AWS, GCP, Azure)
- Environment variable configuration guide
- Secrets management strategy
- Database/storage setup (if needed)
- Monitoring and logging setup guide
- Rollback and disaster recovery procedures

---

## Part 4: Phase 4 Tickets (Monitoring & Maintenance)

**Deadline: February 6th, 2026**

### Epic: MRA2-44 - Phase 4: Monitoring & Maintenance

**Description**: Implement monitoring, drift detection, automated updates, and finalize documentation.

**Subtasks**:

#### MRA2-45: Prometheus/Grafana Monitoring Setup

- **Type**: Task
- **Assignee**: Engineer C
- **Parent**: MRA2-44
- **Priority**: High
- **Description**: 
Set up Prometheus for metrics collection and Grafana for visualization.

**Acceptance Criteria**:

- Prometheus configured to scrape all microservices
- Custom metrics exposed (prediction latency, request count, error rate)
- Grafana dashboards for:
- API performance metrics
- Model performance over time
- System resource usage
- Service health status
- Alerting rules configured (high error rate, high latency)
- Documentation of monitoring setup

#### MRA2-46: Evidently AI Drift Detection

- **Type**: Task
- **Assignee**: Engineer B
- **Parent**: MRA2-44
- **Priority**: High
- **Description**: 
Implement data and model drift detection using Evidently AI.

**Acceptance Criteria**:

- Evidently AI integrated into API service
- Data drift detection (feature distribution changes)
- Model performance drift detection
- Drift reports generated and stored
- Alerts on significant drift detected
- Dashboard showing drift metrics
- Documentation of drift detection strategy

#### MRA2-47: Automated Model Retraining Pipeline

- **Type**: Task
- **Assignee**: Engineer B
- **Parent**: MRA2-44
- **Priority**: High
- **Description**: 
Implement automated model retraining triggered by drift detection or schedule.

**Acceptance Criteria**:

- Scheduled retraining workflow (weekly/monthly)
- Drift-triggered retraining workflow
- Automated model evaluation and comparison
- Automated model promotion to staging (if performance improved)
- Notification system for retraining events
- Rollback mechanism if new model performs worse
- Documentation of retraining strategy

#### MRA2-48: Automated Component Updates

- **Type**: Task
- **Assignee**: Engineer C
- **Parent**: MRA2-44
- **Priority**: Medium
- **Description**: 
Implement automated updates for dependencies and infrastructure components.

**Acceptance Criteria**:

- Dependabot or Renovate configured for dependency updates
- Automated security patch updates
- CI pipeline tests updates before deployment
- Rollback strategy for failed updates
- Update notification system
- Documentation of update process

#### MRA2-49: Technical Documentation Finalization

- **Type**: Task
- **Assignee**: All (coordinated)
- **Parent**: MRA2-44
- **Priority**: High
- **Description**: 
Finalize all technical documentation for the project.

**Acceptance Criteria**:

- Architecture documentation (updated with microservices)
- API documentation (OpenAPI/Swagger)
- Deployment guides
- Operations runbook
- Troubleshooting guide
- Developer onboarding guide
- All documentation reviewed and updated

---

## Part 5: Streamlit Dashboard Tickets

### Epic: MRA2-50 - Streamlit Dashboard with Admin/User Access

**Description**: Build Streamlit dashboard for model predictions with role-based access control (admin and user roles).

**Subtasks**:

#### MRA2-51: Streamlit Dashboard Foundation

- **Type**: Task
- **Assignee**: Engineer C (with support from Engineer B)
- **Parent**: MRA2-50
- **Priority**: High
- **Description**: 
Create basic Streamlit dashboard structure with authentication system.

**Acceptance Criteria**:

- Streamlit app structure (`src/dashboard/app.py` or `streamlit_app.py`)
- User authentication system (session-based or OAuth)
- Role-based access control (admin vs user)
- Login page and session management
- Navigation sidebar with role-based menu items
- Docker container for dashboard (`docker-compose.yml` service: `dashboard`)
- Environment configuration for authentication

#### MRA2-52: User Prediction Interface

- **Type**: Task
- **Assignee**: Engineer C
- **Parent**: MRA2-50
- **Priority**: High
- **Description**: 
Build prediction interface accessible to both users and admins with feature selection.

**Acceptance Criteria**:

- Feature input form with all required features
- Dropdowns/selectors for categorical features
- Number inputs for numerical features
- Date/time pickers for temporal features
- "Predict" button that calls API service
- Prediction result display (class + probability)
- Prediction history (stored in session or database)
- Error handling and validation
- Responsive UI design

#### MRA2-53: Admin Data Management Interface

- **Type**: Task
- **Assignee**: Engineer A (with support from Engineer C)
- **Parent**: MRA2-50
- **Priority**: High
- **Description**: 
Build admin-only interface for fetching new data and triggering data pipeline.

**Acceptance Criteria**:

- Admin-only section (role check)
- "Fetch New Data" button that triggers data service
- Data import status display (progress, logs)
- Data validation results display
- Data version information (DVC)
- Manual data pipeline trigger
- Data preview/exploration tools
- Error handling and notifications

#### MRA2-54: Admin Model Training Interface

- **Type**: Task
- **Assignee**: Engineer B (with support from Engineer C)
- **Parent**: MRA2-50
- **Priority**: High
- **Description**: 
Build admin-only interface for triggering model retraining.

**Acceptance Criteria**:

- Admin-only section (role check)
- "Retrain Model" button that triggers training service
- Training job status display (progress, logs)
- Model selection (which model to retrain)
- Hyperparameter configuration (optional override)
- Training metrics display (real-time updates)
- Model comparison after training
- Model promotion interface (staging → production)
- Error handling and notifications

#### MRA2-55: Dashboard Analytics and Visualization

- **Type**: Task
- **Assignee**: Engineer B
- **Parent**: MRA2-50
- **Priority**: Medium
- **Description**: 
Add analytics and visualization components to dashboard.

**Acceptance Criteria**:

- Model performance metrics visualization (charts)
- Prediction statistics (user/admin views)
- Data quality metrics (admin only)
- Model comparison charts (admin only)
- Historical performance trends
- Export functionality for reports
- Interactive charts (Plotly or similar)

#### MRA2-56: Dashboard Integration with Services

- **Type**: Task
- **Assignee**: Engineer C
- **Parent**: MRA2-50
- **Priority**: High
- **Description**: 
Integrate dashboard with all microservices (API, Training, Data).

**Acceptance Criteria**:

- Dashboard calls API service for predictions
- Dashboard calls training service for retraining
- Dashboard calls data service for data operations
- Error handling for service unavailability
- Loading states and progress indicators
- Service health status display
- Configuration for service endpoints

#### MRA2-57: Dashboard Authentication and Security

- **Type**: Task
- **Assignee**: Engineer C
- **Parent**: MRA2-50
- **Priority**: High
- **Description**: 
Implement secure authentication and authorization for dashboard.

**Acceptance Criteria**:

- Secure password storage (hashed)
- Session management with expiration
- Role-based access control enforcement
- CSRF protection
- Input validation and sanitization
- Audit logging for admin actions
- User management interface (admin only)
- Password reset functionality

---

## Summary of New Tickets

**Phase 2 (9 tickets)**:

- 1 Epic (MRA2-28)
- 8 Tasks (MRA2-29 to MRA2-36)

**Phase 3 (7 tickets)**:

- 1 Epic (MRA2-37)
- 6 Tasks (MRA2-38 to MRA2-43)

**Phase 4 (6 tickets)**:

- 1 Epic (MRA2-44)
- 5 Tasks (MRA2-45 to MRA2-49)

**Streamlit Dashboard (8 tickets)**:

- 1 Epic (MRA2-50)
- 7 Tasks (MRA2-51 to MRA2-57)

**Total: 30 new tickets**

---

## Implementation Notes

1. **Streamlit Dashboard Placement**: Can be added in Phase 2 or Phase 3 depending on priority. Recommend Phase 2 for early user feedback.

2. **Microservices Decision**: Ticket MRA2-27 should be resolved first to determine if microservices are needed or if a simpler architecture suffices.

3. **Authentication Strategy**: For Streamlit, consider:

- Simple: Session-based auth with config file for users
- Advanced: OAuth2 integration or database-backed auth
- Recommendation: Start simple, enhance in Phase 3

4. **Service Communication**: Start with REST APIs, add message queues later if needed for async operations.

5. **Dependencies**: Ensure all new services are added to `docker-compose.yml` and `pyproject.toml`.