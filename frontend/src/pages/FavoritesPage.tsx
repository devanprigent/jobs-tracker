import { useEffect, useState } from "react";

import { getApplications, getCompanies, updateApplication } from "../api";
import ApplicationForm from "../components/ApplicationForm";
import ApplicationTable from "../components/ApplicationTable";
import type { Application, ApplicationInput, ApplicationState, Status } from "../types";

export default function FavoritesPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [companies, setCompanies] = useState<string[]>([]);
  const [editingApplication, setEditingApplication] = useState<Application | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [status, setStatus] = useState<Status>({ loading: true, error: "" });

  useEffect(() => {
    loadFavorites();
  }, []);

  async function loadFavorites() {
    setStatus({ loading: true, error: "" });
    try {
      const [nextApplications, nextCompanies] = await Promise.all([
        getApplications({ favorite: true }),
        getCompanies(),
      ]);
      setApplications(nextApplications);
      setCompanies(nextCompanies);
      setStatus({ loading: false, error: "" });
    } catch (error) {
      setStatus({ loading: false, error: getErrorMessage(error) });
    }
  }

  async function handleStateChange(application: Application, state: ApplicationState) {
    try {
      await updateApplication({ ...application, state });
      await loadFavorites();
    } catch (error) {
      setStatus({ loading: false, error: getErrorMessage(error) });
    }
  }

  async function handleSubmit(application: ApplicationInput) {
    if (!application.id) {
      return;
    }

    try {
      await updateApplication({ ...application, id: application.id });
      closeForm();
      await loadFavorites();
    } catch (error) {
      setStatus({ loading: false, error: getErrorMessage(error) });
    }
  }

  function openEditForm(application: Application) {
    setEditingApplication(application);
    setIsFormOpen(true);
  }

  function closeForm() {
    setEditingApplication(null);
    setIsFormOpen(false);
  }

  return (
    <section className="page-grid">
      {isFormOpen ? (
        <div className="modal-backdrop" role="presentation" onMouseDown={closeForm}>
          <div
            className="modal-panel"
            role="dialog"
            aria-modal="true"
            aria-labelledby="favorite-form-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className="modal-header">
              <h3 id="favorite-form-title">Edit</h3>
            </div>
            <ApplicationForm
              companyOptions={companies}
              initialValues={editingApplication}
              onSubmit={handleSubmit}
              onCancel={closeForm}
              submitLabel="Save"
            />
          </div>
        </div>
      ) : null}

      <section className="card">
        <div className="section-heading">
          <h3>Favorites</h3>
          {status.loading ? <span>Loading...</span> : <span>{applications.length} favorite</span>}
        </div>
        {status.error ? <p className="error-message">{status.error}</p> : null}
        {!status.loading ? (
          <ApplicationTable
            applications={applications}
            emptyMessage="No favorites yet."
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
