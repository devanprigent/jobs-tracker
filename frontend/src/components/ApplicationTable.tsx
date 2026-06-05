import { APPLICATION_STATES, type Application, type ApplicationState } from "../types";

function PencilIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <path d="M4 16.5V20h3.5L18.1 9.4l-3.5-3.5L4 16.5Z" />
      <path d="m16 4.5 1.2-1.2a1 1 0 0 1 1.4 0l2.1 2.1a1 1 0 0 1 0 1.4L19.5 8 16 4.5Z" />
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <path d="M9 4h6l1 2h4v2H4V6h4l1-2Z" />
      <path d="M6 10h12l-1 10H7L6 10Z" />
    </svg>
  );
}

type ApplicationTableProps = {
  applications: Application[];
  emptyMessage: string;
  onDelete?: (id: number) => void;
  onEdit?: (application: Application) => void;
  onStateChange: (application: Application, state: ApplicationState) => void;
};

export default function ApplicationTable({
  applications,
  emptyMessage,
  onDelete,
  onEdit,
  onStateChange,
}: ApplicationTableProps) {
  if (applications.length === 0) {
    return <p className="empty-state">{emptyMessage}</p>;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Position</th>
            <th>Company</th>
            <th>Location</th>
            <th>State</th>
            <th>Date</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {applications.map((application) => (
            <tr key={application.id}>
              <td>{application.position}</td>
              <td>{application.company}</td>
              <td>{[application.city, application.country].filter(Boolean).join(", ") || "-"}</td>
              <td>
                <select
                  value={application.state}
                  onChange={(event) => onStateChange(application, event.target.value as ApplicationState)}
                  aria-label={`State for ${application.position}`}
                >
                  {APPLICATION_STATES.map((state) => (
                    <option key={state} value={state}>
                      {state}
                    </option>
                  ))}
                </select>
              </td>
              <td>{application.candidature_date}</td>
              <td>
                <div className="row-actions">
                  {onEdit ? (
                    <button
                      type="button"
                      className="icon-button"
                      aria-label={`Edit ${application.position}`}
                      onClick={() => onEdit(application)}
                    >
                      <PencilIcon />
                    </button>
                  ) : null}
                  {onDelete ? (
                    <button
                      type="button"
                      className="icon-button danger-icon"
                      aria-label={`Delete ${application.position}`}
                      onClick={() => onDelete(application.id)}
                    >
                      <TrashIcon />
                    </button>
                  ) : null}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
