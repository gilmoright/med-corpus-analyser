import React, { useState, Fragment } from "react";
import MedForm from "./MedForm";
import MedTable from "./MedTable";

var res_fetch;

const requestFunction = (input) => {
    var tablePseudoData = [{
        "Drugnames": "dsad",
        "Diseasenames": "sfafasf",
        "Indications": "hfdhdafh",
        "ADRs": "dsad",
        "ADR_reviews_count": 2,
        "Pos_reviews_count": 3,
        "Neg_reviews_count": 1,
        "Negated_ADE_reviews_count": 0,
        "Review_count": 4,
        "Review_urls": ["dsfdf"],
    }]
    //return tablePseudoData
    return fetch('./scheme2_request/', {
        method: 'POST',
        body: JSON.stringify(input)
        
    }).then((response) => {
        if (response.status >= 200 && response.status < 300) {
            return response.json();
        } else {
            let error = new Error(response.statusText);
            error.response = response;
            throw error;
        }
    })
        .then((data) => { res_fetch = data })
        .catch((e) => {
            console.log('Error: ' + e.message);
            console.log(e.response);
            res_fetch = 'Ошибка при запросе к серверу.';
        });
}

function Profile() {
    const [tableData, setTableData] = useState([]);
    const [formObject, setFormObject] = useState({
        Drugnames: "",
        Diseasenames: "",
        Indications: "",
        ADRs: ""
    });

    

    const onValChange = (event) => {
        const value = (res) => ({
            ...res,
            [event.target.name]: event.target.value,
        });
        setFormObject(value);
    };
    const onFormSubmit = (event) => {
        event.preventDefault();
        const checkVal = !Object.values(formObject).every((res) => res === "");
        if (checkVal) {
            const dataObj = (data) => [...data, formObject];
            //var tableContent = requestFunction(formObject);
            //console.log(tableContent)
            //setTableData(tableContent);
            requestFunction(formObject).then(() => {
                if (res_fetch==='Ошибка при запросе к серверу.') {
                    setTableData([]);
                    return;
                }
            console.log(res_fetch)
            setTableData(res_fetch);
            });

            const isEmpty = { Drugnames: "", Diseasenames: "", Indications: "", ADRs: "" };
            setFormObject(isEmpty);
        }
    };
    
    return (
        <Fragment>
            <MedForm
                onValChange={onValChange}
                formObject={formObject}
                onFormSubmit={onFormSubmit}
            />
            <MedTable tableData={tableData} />
        </Fragment>
    );
}
export default Profile;