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
        uint256 doctorId;  // Added doctor ID
    }

    struct OffChainDiagnosis {
        string hash;         // Hash des données off-chain (par ex. IPFS)
        uint256 timestamp;   // Date d'enregistrement
    }

    // Stockage on-chain des diagnostics détaillés par diagnosis ID
    mapping(uint256 => DetailedDiagnosis) private diagnoses;
    uint256 private diagnosisCount; // Track number of diagnoses

    // Stockage off-chain par diagnosis ID
    mapping(uint256 => OffChainDiagnosis) private offChainDiagnoses;

    // Événement pour signaler l'enregistrement off-chain
    event DiagnosisRecorded(uint256 indexed diagnosisId, string hash);
    // Événement pour signaler l'ajout d'un diagnostic
    event DiagnosisAdded(uint256 indexed diagnosisId, uint256 patientId, uint256 doctorId);

    // 🔹 Ajouter un diagnostic complet on-chain
    function addDiagnosis(
        uint256 _diagnosisId,
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
        require(diagnoses[_diagnosisId].date == 0, "Diagnosis ID already exists");
        diagnoses[_diagnosisId] = DetailedDiagnosis(
            _condition1, _confidence1,
            _condition2, _confidence2,
            _condition3, _confidence3,
            _doctorDiagnosis,
            block.timestamp,
            _patientId,
            _doctorId
        );
        diagnosisCount++;
        emit DiagnosisAdded(_diagnosisId, _patientId, _doctorId);
    }

    // 🔹 Lier avec le backend via hash (off-chain data)
    function storeDiagnosisHash(uint256 diagnosisId, string memory diagnosisHash) public {
        require(bytes(diagnosisHash).length > 0, "Hash is required");
        offChainDiagnoses[diagnosisId] = OffChainDiagnosis(diagnosisHash, block.timestamp);
        emit DiagnosisRecorded(diagnosisId, diagnosisHash);
    }

    // 🔹 Récupérer le hash d’un diagnostic off-chain
    function getDiagnosisHash(uint256 diagnosisId) public view returns (string memory, uint256) {
        OffChainDiagnosis memory d = offChainDiagnoses[diagnosisId];
        return (d.hash, d.timestamp);
    }

    // 🔹 Récupérer un diagnostic on-chain par diagnosis ID
    function getDiagnosis(uint256 diagnosisId) public view returns (
        string memory, uint256,
        string memory, uint256,
        string memory, uint256,
        string memory, uint256, uint256, uint256
    ) {
        require(diagnoses[diagnosisId].date != 0, "Diagnosis does not exist");
        DetailedDiagnosis memory d = diagnoses[diagnosisId];
        return (
            d.condition1, d.confidence1,
            d.condition2, d.confidence2,
            d.condition3, d.confidence3,
            d.doctorDiagnosis,
            d.date,
            d.patientId,
            d.doctorId
        );
    }

    // 🔹 Nombre total de diagnostics
    function getDiagnosisCount() public view returns (uint256) {
        return diagnosisCount;
    }
}