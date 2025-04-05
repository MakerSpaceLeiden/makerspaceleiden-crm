# Contributing Guide

This document outlines the workflow for contributors and maintainers when submitting and evaluating changes to the project.

## Getting Started

### Pre-commit

In order to install pre-commit, either use it via the created environment in Poetry, or install it globally using either `pip` or `pipx`.

Then run `pre-commit install` in order to install the hooks.

## Maintainer Workflow

When evaluating submissions and pull requests, please follow these guidelines:

### Types of Changes and Review Requirements

1. **Minor Changes**
   - Cosmetic code changes, test modifications, documentation updates
   - You can merge these to main/master/head yourself
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

If you want to deploy changes to production:
- Contact the deployment team (such as @dirkx or @Younday)
- They will guide you through the deployment process

## Questions and Support

If you have any questions about the contribution process, please reach out to the project maintainers.

Thank you for your contributions!
