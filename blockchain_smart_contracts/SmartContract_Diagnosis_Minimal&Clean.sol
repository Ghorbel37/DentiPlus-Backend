// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.8.6 <0.9.0;

/**
 * @title FullDiagnosisContract
 * @dev Contrat de stockage pour les diagnostics médicaux optimisé avec mappings
 */

contract FullDiagnosisContract {
    struct DetailedDiagnosis {
        uint256 id;
        string condition1;
        uint256 confidence1;
        string condition2;
        uint256 confidence2;
        string condition3;
        uint256 confidence3;
        string doctorDiagnosis;
        uint256 date;
        uint256 patientId;
        uint256 doctorId;
    }

    // Mappings pour remplacer les tableaux
    mapping(uint256 => DetailedDiagnosis) private diagnosisById;

    // Événements
    event DiagnosisAdded(
        uint256 indexed diagnosisId,
        uint256 indexed patientId
    );

    // Ajouter un diagnostic complet on-chain
    function addDiagnosis(
        uint256 _id,
        string memory _condition1,
        uint256 _confidence1,
        string memory _condition2,
        uint256 _confidence2,
        string memory _condition3,
        uint256 _confidence3,
        string memory _doctorDiagnosis,
        uint256 _patientId,
        uint256 _doctorId
    ) public {
        // Vérifier que l'ID n'existe pas déjà
        require(diagnosisById[_id].id == 0, "Diagnosis ID already exists");

        // Créer et stocker le diagnostic
        DetailedDiagnosis memory d = DetailedDiagnosis(
            _id,
            _condition1,
            _confidence1,
            _condition2,
            _confidence2,
            _condition3,
            _confidence3,
            _doctorDiagnosis,
            block.timestamp,
            _patientId,
            _doctorId
        );

        diagnosisById[_id] = d;
        emit DiagnosisAdded(_id, _patientId);
    }

    // Récupérer un diagnostic on-chain par id
    function getDiagnosisId(
        uint256 _id
    )
        public
        view
        returns (
            uint256,
            string memory,
            uint256,
            string memory,
            uint256,
            string memory,
            uint256,
            string memory,
            uint256,
            uint256,
            uint256
        )
    {
        DetailedDiagnosis memory d = diagnosisById[_id];
        require(d.id != 0, "Diagnosis ID not found");

        return (
            d.id,
            d.condition1,
            d.confidence1,
            d.condition2,
            d.confidence2,
            d.condition3,
            d.confidence3,
            d.doctorDiagnosis,
            d.date,
            d.patientId,
            d.doctorId
        );
    }
}
