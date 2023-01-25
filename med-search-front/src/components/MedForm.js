function MedForm({ onValChange, formObject, onFormSubmit }) {
    return (
        <div className="row mb-4">
            <div className="text_form">
                <input
                    type="text"
                    className="form-control"
                    placeholder="Drugname"
                    onChange={onValChange}
                    value={formObject.Drugnames}
                    name="Drugnames"
                />
            </div>
            <div className="text_form">
                <input
                    type="text"
                    className="form-control"
                    placeholder="Diseasename"
                    onChange={onValChange}
                    value={formObject.Diseasenames}
                    name="Diseasenames"
                />
            </div>
            <div className="text_form">
                <input
                    type="text"
                    className="form-control"
                    placeholder="Indication"
                    onChange={onValChange}
                    value={formObject.Indications}
                    name="Indications"
                />
            </div>
            <div className="text_form">
                <input
                    type="text"
                    className="form-control"
                    placeholder="ADR"
                    onChange={onValChange}
                    value={formObject.ADRs}
                    name="ADRs"
                />
            </div>
            <div className="d-grid">
                <input
                    type="submit"
                    onClick={onFormSubmit}
                    className="btn btn-success"
                />
            </div>
        </div>
    );
}
export default MedForm;