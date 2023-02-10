function MedTable({ tableData }) {
    return (
        <table className="table">
            <thead>
                <tr>
                    <th>Drugname</th>
                    <th>Diseasename</th>
                    <th>Indication</th>
                    <th>ADR</th>
                    <th>ADR reviews count</th>
                    <th>Pos reviews count</th>
                    <th>Negative reviews count</th>
                    <th>Negated reviews count</th>
                    <th>Reviews count</th>
                    <th>Review urls</th>
                </tr>
            </thead>
            <tbody>
                {tableData.map((data, index) => {
                    return (
                        <tr key={index}>
                            <td>{data.Drugnames}</td>
                            <td>{data.Diseasenames}</td>
                            <td>{data.Indications}</td>
                            <td>{data.ADRs}</td>
                            <td>{data.ADR_reviews_count}</td>
                            <td>{data.Pos_reviews_countg}</td>
                            <td>{data.Neg_reviews_count}</td>
                            <td>{data.Negated_ADE_reviews_count}</td>
                            <td>{data.Review_count}</td>
                            <td>{data.Review_urls}</td>
                        </tr>
                    );
                })}
            </tbody>
        </table>
    );
}
export default MedTable;
