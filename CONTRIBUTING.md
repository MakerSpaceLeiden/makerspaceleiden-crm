# Contributing Guide

This document outlines the workflow for contributors and maintainers when submitting and evaluating changes to the project.

## Getting Started

### Pre-commit

In order to install pre-commit, either use it via the created environment in `uv`

Then run `pre-commit install` in order to install the hooks.

## Development Workflow

Our project follows this branch structure:

- Features are developed in feature branches
- Feature branches are merged into `master` after review
- `master` is later merged into `prod` for production deployments

## Maintainer Workflow

When evaluating submissions and pull requests, please follow these guidelines:

### Types of Changes and Review Requirements

1. **Minor Changes**
   - Cosmetic code changes, test modifications, documentation updates
   - You can merge these to `master` yourself
   - If unsure, wait 24-48 hours for others to provide feedback

2. **Module-Level Changes**
   - When changes affect core functionality of a specific module
   - Allow adequate time (at least 48 hours) for other maintainers to review

3. **Core Changes**
   - Changes that affect core code, safety features, financial components, or similar critical areas
   - Require review and merge by someone other than the proposer
   - Do not merge your own changes in these categories

4. **Sensitive/Setting Changes**
   - Changes to limits or settings related to financial components
   - Require explicit approval from trustees
   - Tag trustees in the pull request for visibility and permission

## Deployment Process

Changes are manually deployed to production, if you would like to deploy updates, please contact either @dirkx or @Younday directly.

The process for deploying changes to production:

**Production Deployment**
   - Contact the deployment team (such as @dirkx or @Younday) for assistance
   - Standard deployment process:
     ```
     git status  # Check current state
     git pull    # Pull latest changes from prod branch
     sh rollout-prod.sh  # Script makes backup, runs migrations, and restarts services
     ```

**Production Hotfixes**
   - Small corrections can be made directly on the production system
   - These changes should be:
     - Pushed back to the `prod` branch if they are minor
     - Later synchronized into `master`
     - For larger changes, create a proper feature branch instead


## Questions and Support

If you have any questions about the contribution process, please reach out to the project maintainers.

Thank you for your contributions!
