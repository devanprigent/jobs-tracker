import type { DragEvent } from "react";

import { APPLICATION_STATES, type Application, type ApplicationState } from "../types";

function PencilIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <path d="M4 16.5V20h3.5L18.1 9.4l-3.5-3.5L4 16.5Z" />
      <path d="m16 4.5 1.2-1.2a1 1 0 0 1 1.4 0l2.1 2.1a1 1 0 0 1 0 1.4L19.5 8 16 4.5Z" />
    </svg>
  );
}

type ApplicationKanbanProps = {
  applications: Application[];
  emptyMessage: string;
  onEdit: (application: Application) => void;
  onStateChange: (application: Application, state: ApplicationState) => void;
};

export default function ApplicationKanban({
  applications,
  emptyMessage,
  onEdit,
  onStateChange,
}: ApplicationKanbanProps) {
  if (applications.length === 0) {
    return <p className="empty-state">{emptyMessage}</p>;
  }

  function handleDragStart(event: DragEvent<HTMLElement>, application: Application) {
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("applicationId", String(application.id));
  }

  function handleDrop(event: DragEvent<HTMLElement>, state: ApplicationState) {
    event.preventDefault();
    const applicationId = Number(event.dataTransfer.getData("applicationId"));
    const application = applications.find((item) => item.id === applicationId);

    if (!application || application.state === state) {
      return;
    }

    onStateChange(application, state);
  }

  return (
    <div className="kanban-board">
      {APPLICATION_STATES.map((state) => {
        const columnApplications = applications.filter((application) => application.state === state);

        return (
          <section
            key={state}
            className="kanban-column"
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => handleDrop(event, state)}
          >
            <div className="kanban-column-header">
              <h4>{state}</h4>
              <span>{columnApplications.length}</span>
            </div>

            <div className="kanban-cards">
              {columnApplications.map((application) => (
                <article
                  key={application.id}
                  className="kanban-card"
                  draggable
                  onDragStart={(event) => handleDragStart(event, application)}
                >
                  <div>
                    <h5>{application.position}</h5>
                    <p>{application.company}</p>
                  </div>
                  <div className="kanban-card-footer">
                    <span className="kanban-date">{application.candidature_date}</span>
                    <div className="card-actions">
                      <button
                        type="button"
                        className="icon-button"
                        aria-label={`Edit ${application.position}`}
                        onClick={() => onEdit(application)}
                      >
                        <PencilIcon />
                      </button>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
