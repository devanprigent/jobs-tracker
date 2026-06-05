import type { ChangeEvent, FormEvent } from "react";
import { useEffect, useState } from "react";

import { APPLICATION_STATES, type ApplicationInput } from "../types";

function today() {
  return new Date().toISOString().slice(0, 10);
}

const EMPTY_FORM: ApplicationInput = {
  position: "",
  company: "",
  country: "",
  city: "",
  state: "Applied",
  candidature_date: today(),
  favorite: false,
};

type ApplicationFormProps = {
  companyOptions?: string[];
  initialValues?: ApplicationInput | null;
  onSubmit: (application: ApplicationInput) => Promise<void>;
  onCancel?: () => void;
  submitLabel?: string;
};

export default function ApplicationForm({
  companyOptions = [],
  initialValues,
  onSubmit,
  onCancel,
  submitLabel = "Add",
}: ApplicationFormProps) {
  const [form, setForm] = useState<ApplicationInput>(EMPTY_FORM);

  useEffect(() => {
    setForm(initialValues ?? EMPTY_FORM);
  }, [initialValues]);

  function updateField(event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    const { name, type, value } = event.target;
    const nextValue = type === "checkbox" ? (event.target as HTMLInputElement).checked : value;

    setForm((current) => ({
      ...current,
      [name]: nextValue,
    }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit(form);
    if (!initialValues) {
      setForm(EMPTY_FORM);
    }
  }

  return (
    <form className="card form-grid" onSubmit={handleSubmit}>
      <label>
        Position
        <input name="position" value={form.position} onChange={updateField} placeholder="Role" required />
      </label>

      <label>
        Company
        <input
          name="company"
          value={form.company}
          onChange={updateField}
          placeholder="Acme"
          list="company-options"
          required
        />
        <datalist id="company-options">
          {companyOptions.map((company) => (
            <option key={company} value={company} />
          ))}
        </datalist>
      </label>

      <label>
        Country
        <input name="country" value={form.country} onChange={updateField} placeholder="France" />
      </label>

      <label>
        City
        <input name="city" value={form.city} onChange={updateField} placeholder="Paris" />
      </label>

      <label>
        State
        <select name="state" value={form.state} onChange={updateField}>
          {APPLICATION_STATES.map((state) => (
            <option key={state} value={state}>
              {state}
            </option>
          ))}
        </select>
      </label>

      <label>
        Date
        <input name="candidature_date" type="date" value={form.candidature_date} onChange={updateField} required />
      </label>

      <label className="checkbox-label">
        <input name="favorite" type="checkbox" checked={form.favorite} onChange={updateField} />
        Favorite
      </label>

      <div className="form-actions">
        {onCancel ? (
          <button type="button" className="secondary" onClick={onCancel}>
            Cancel
          </button>
        ) : null}
        <button type="submit" className="save-action">
          {submitLabel}
        </button>
      </div>
    </form>
  );
}
