// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.8.6 <0.9.0;

/**
 * @title Storage
 * @dev Store & retrieve value in a variable
 * @custom:dev-run-script ./scripts/deploy_with_ethers.ts
 */



contract FullDiagnosisContract {
    
    struct DetailedDiagnosis {
        string condition1;
        uint256 confidence1;
        string condition2;
        uint256 confidence2;
        string condition3;
        uint256 confidence3;
        string doctorDiagnosis;
        uint256 date;
        uint256 patientId;
    }

    struct OffChainDiagnosis {
        string hash;         // Hash des données off-chain (par ex. IPFS)
        uint256 timestamp;   // Date d'enregistrement
    }

    // Stockage on-chain des diagnostics détaillés
    DetailedDiagnosis[] private diagnoses;

    // Stockage off-chain par patient ID
    mapping(uint256 => OffChainDiagnosis) public offChainDiagnoses;

    // Événement pour signaler l'enregistrement off-chain
    event DiagnosisRecorded(uint256 indexed patientId, string hash);

    // 🔹 Ajouter un diagnostic complet on-chain
    function addDiagnosis(
        string memory _condition1,
        uint256 _confidence1,
        string memory _condition2,
        uint256 _confidence2,
        string memory _condition3,
        uint256 _confidence3,
        string memory _doctorDiagnosis,
        uint256 _patientId
    ) public {
        diagnoses.push(DetailedDiagnosis(
            _condition1, _confidence1,
            _condition2, _confidence2,
            _condition3, _confidence3,
            _doctorDiagnosis,
            block.timestamp,
            _patientId
        ));
    }

    // 🔹 Lier avec le backend via hash (off-chain data)
    function storeDiagnosisHash(uint256 patientId, string memory diagnosisHash) public {
        require(bytes(diagnosisHash).length > 0, "Hash is required");
        offChainDiagnoses[patientId] = OffChainDiagnosis(diagnosisHash, block.timestamp);
        emit DiagnosisRecorded(patientId, diagnosisHash);
    }

    // 🔹 Récupérer le hash d’un diagnostic off-chain
    function getDiagnosisHash(uint256 patientId) public view returns (string memory, uint256) {
        OffChainDiagnosis memory d = offChainDiagnoses[patientId];
        return (d.hash, d.timestamp);
    }

    // 🔹 Récupérer un diagnostic on-chain par index
    function getDiagnosis(uint index) public view returns (
        string memory, uint256,
        string memory, uint256,
        string memory, uint256,
        string memory, uint256, uint256
    ) {
        DetailedDiagnosis memory d = diagnoses[index];
        return (
            d.condition1, d.confidence1,
            d.condition2, d.confidence2,
            d.condition3, d.confidence3,
            d.doctorDiagnosis,
            d.date,
            d.patientId
        );
    }

    // 🔹 Liste des confidences // il *3 hekom khatir aandik 3 confiance 
    function getAllConfidences() public view returns (uint256[] memory) {
        uint256[] memory confs = new uint256[](diagnoses.length * 3);
        for (uint i = 0; i < diagnoses.length; i++) {
            confs[i * 3] = diagnoses[i].confidence1;
            confs[i * 3 + 1] = diagnoses[i].confidence2;
            confs[i * 3 + 2] = diagnoses[i].confidence3;
        }
        return confs;
    }

    // 🔹 Liste des conditions
    function getAllConditions() public view returns (string[] memory) {
        string[] memory conds = new string[](diagnoses.length * 3);
        for (uint i = 0; i < diagnoses.length; i++) {
            conds[i * 3] = diagnoses[i].condition1;
            conds[i * 3 + 1] = diagnoses[i].condition2;
            conds[i * 3 + 2] = diagnoses[i].condition3;
        }
        return conds;
    }

    // 🔹 Liste des IDs de patients
    function getAllPatientIds() public view returns (uint256[] memory) {
        uint256[] memory ids = new uint256[](diagnoses.length);
        for (uint i = 0; i < diagnoses.length; i++) {
            ids[i] = diagnoses[i].patientId;
        }
        return ids;
    }
    //ajouter un element lil liste
    function addElementDiagnosis(
    string memory _condition1,
    uint256 _confidence1,
    string memory _condition2,
    uint256 _confidence2,
    string memory _condition3,
    uint256 _confidence3,
    string memory _doctorDiagnosis,
    uint256 _patientId
    ) public {
    diagnoses.push(DetailedDiagnosis(
        _condition1, _confidence1,
        _condition2, _confidence2,
        _condition3, _confidence3,
        _doctorDiagnosis,
        block.timestamp,       // auto génère la date
        _patientId
    ));
    }


    // 🔹 Nombre total de diagnostics
    function getDiagnosisCount() public view returns (uint) {
        return diagnoses.length;
    }
}
