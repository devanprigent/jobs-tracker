import { useEffect, useState } from "react";

import { createApplication, deleteApplication, getApplications, getCompanies, updateApplication } from "../api";
import ApplicationForm from "../components/ApplicationForm";
import ApplicationKanban from "../components/ApplicationKanban";
import type { Application, ApplicationInput, ApplicationState, Status } from "../types";

function TrashIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <path d="M9 4h6l1 2h4v2H4V6h4l1-2Z" />
      <path d="M6 10h12l-1 10H7L6 10Z" />
    </svg>
  );
}

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [companies, setCompanies] = useState<string[]>([]);
  const [editingApplication, setEditingApplication] = useState<Application | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [status, setStatus] = useState<Status>({ loading: true, error: "" });

  useEffect(() => {
    loadApplications();
  }, []);

  async function loadApplications() {
    setStatus({ loading: true, error: "" });
    try {
      const [nextApplications, nextCompanies] = await Promise.all([getApplications(), getCompanies()]);
      setApplications(nextApplications);
      setCompanies(nextCompanies);
      setStatus({ loading: false, error: "" });
    } catch (error) {
      setStatus({ loading: false, error: getErrorMessage(error) });
    }
  }

  async function handleSubmit(application: ApplicationInput) {
    try {
      if (application.id) {
        await updateApplication({ ...application, id: application.id });
      } else {
        await createApplication(application);
      }
      closeForm();
      await loadApplications();
    } catch (error) {
      setStatus({ loading: false, error: getErrorMessage(error) });
    }
  }

  function openAddForm() {
    setEditingApplication(null);
    setIsFormOpen(true);
  }

  function openEditForm(application: Application) {
    setEditingApplication(application);
    setIsFormOpen(true);
  }

  function closeForm() {
    setEditingApplication(null);
    setIsFormOpen(false);
  }

  async function handleStateChange(application: Application, state: ApplicationState) {
    await handleSubmit({ ...application, state });
  }

  async function handleDelete(id: number) {
    try {
      await deleteApplication(id);
      closeForm();
      await loadApplications();
    } catch (error) {
      setStatus({ loading: false, error: getErrorMessage(error) });
    }
  }

  return (
    <section className="page-grid">
      <div className="page-heading action-only">
        <button type="button" className="add-application-button" onClick={openAddForm}>
          Add
        </button>
      </div>

      {isFormOpen ? (
        <div className="modal-backdrop" role="presentation" onMouseDown={closeForm}>
          <div
            className="modal-panel"
            role="dialog"
            aria-modal="true"
            aria-labelledby="application-form-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className="modal-header">
              <h3 id="application-form-title">{editingApplication ? "Edit" : "Add"}</h3>
              {editingApplication ? (
                <button
                  type="button"
                  className="icon-button danger-icon"
                  aria-label={`Delete ${editingApplication.position}`}
                  onClick={() => handleDelete(editingApplication.id)}
                >
                  <TrashIcon />
                </button>
              ) : null}
            </div>
            <ApplicationForm
              companyOptions={companies}
              initialValues={editingApplication}
              onSubmit={handleSubmit}
              onCancel={closeForm}
              submitLabel={editingApplication ? "Save" : "Add"}
            />
          </div>
        </div>
      ) : null}

      <section className="card">
        <div className="section-heading">
          <h3>Applications</h3>
          {status.loading ? <span>Loading...</span> : <span>{applications.length} total</span>}
        </div>
        {status.error ? <p className="error-message">{status.error}</p> : null}
        {!status.loading ? (
          <ApplicationKanban
            applications={applications}
            emptyMessage="No applications yet."
            onEdit={openEditForm}
            onStateChange={handleStateChange}
          />
        ) : null}
      </section>
    </section>
  );
}

function getErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Unexpected error";
}
