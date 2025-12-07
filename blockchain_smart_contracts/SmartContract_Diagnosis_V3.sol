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

    struct OffChainDiagnosis {
        string hash;         // Hash des données off-chain
        uint256 timestamp;   // Date d'enregistrement
        uint256 patientId;   // Patient concerné
        uint256 diagnosisId; // ID du diagnostic concerné
    }

    // Mappings pour remplacer les tableaux
    mapping(uint256 => DetailedDiagnosis) private diagnosisById;
    mapping(uint256 => OffChainDiagnosis) private offChainDiagnosesByPatient;
    //stocke plusieurs hashs pour un m diagnostic 
    mapping(uint256 => mapping(uint256 => OffChainDiagnosis)) private offChainHashesByDiagnosisId;
    
    // Variables pour suivre les compteurs
    //Compteur global des diagnostics enregistrés.
    uint256 public diagnosisCount = 0;
    //Garde en mémoire combien de hashs sont liés à un diagnostic.
    mapping(uint256 => uint256) private hashCountByDiagnosisId;
    
    // Nouveaux mappings pour faciliter les requêtes
    //Associe un index (0, 1, 2…) à un ID de diagnostic pour itération
    mapping(uint256 => uint256) private diagnosisIdsByIndex;
    //retrouver facilement tous les hashs d’un diagnostic.
    mapping(uint256 => mapping(uint256 => string)) private hashesForDiagnosis;

    // Événements
    event HashAdded(string hash, uint256 indexed patientId, uint256 indexed diagnosisId, uint256 timestamp);
    event DiagnosisAdded(uint256 indexed diagnosisId, uint256 indexed patientId);

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
            _condition1, _confidence1,
            _condition2, _confidence2,
            _condition3, _confidence3,
            _doctorDiagnosis,
            block.timestamp,
            _patientId,
            _doctorId
        );
        
        diagnosisById[_id] = d;
        diagnosisIdsByIndex[diagnosisCount] = _id;
        diagnosisCount++;
        
        emit DiagnosisAdded(_id, _patientId);
    }

    // Lier avec le backend via hash (off-chain data)
    function storeDiagnosisHash(uint256 patientId, string memory diagnosisHash) public {
        require(bytes(diagnosisHash).length > 0, "Hash is required");
        offChainDiagnosesByPatient[patientId] = OffChainDiagnosis(
            diagnosisHash, 
            block.timestamp, 
            patientId, 
            0
        );
    }

    // Récupérer le hash d'un diagnostic off-chain
    function getDiagnosisHash(uint256 patientId) public view returns (string memory, uint256) {
        OffChainDiagnosis memory d = offChainDiagnosesByPatient[patientId];
        return (d.hash, d.timestamp);
    }

    // Récupérer les hash off-chain par l'ID du diagnostic
    function getHashesById(uint256 _diagnosisId) public view returns (string[] memory) {
        uint256 count = hashCountByDiagnosisId[_diagnosisId];
        string[] memory hashes = new string[](count);
        
        for(uint256 i = 0; i < count; i++) {
            hashes[i] = hashesForDiagnosis[_diagnosisId][i];
        }
        
        return hashes;
    }

    // Enregistrer un hash off-chain lié à un diagnostic
    function addOffChainHashByDiagnosisId(string memory _hash, uint256 _diagnosisId) public {
        require(bytes(_hash).length > 0, "Hash is required");
        
        // Vérifier que le diagnostic existe
        require(diagnosisById[_diagnosisId].id != 0, "Diagnosis ID not found");
        
        // Récupérer le patientId associé
        uint256 patientId = diagnosisById[_diagnosisId].patientId;
        
        // Vérifier que le hash n'existe pas déjà
        //fi Solidity, manajmouch ncompariw deux string toul bi ==,
    // donc ncompariw leurs hashs avec keccak256( standard et sécurisé)
        uint256 hashCount = hashCountByDiagnosisId[_diagnosisId];
        for(uint256 i = 0; i < hashCount; i++) {
            require(
                keccak256(bytes(hashesForDiagnosis[_diagnosisId][i])) != keccak256(bytes(_hash)), 
                "Hash already exists"
            );
        }
        
        // Stocker le hash
        OffChainDiagnosis memory newHash = OffChainDiagnosis(
            _hash,
            block.timestamp,
            patientId,
            _diagnosisId
        );
        
        offChainHashesByDiagnosisId[_diagnosisId][hashCount] = newHash;
        hashesForDiagnosis[_diagnosisId][hashCount] = _hash;
        hashCountByDiagnosisId[_diagnosisId]++;
        
        emit HashAdded(_hash, patientId, _diagnosisId, block.timestamp);
    }

    // Récupérer un diagnostic on-chain par id
    function getDiagnosisId(uint256 _id) public view returns (
        uint256,
        string memory, uint256,
        string memory, uint256,
        string memory, uint256,
        string memory, uint256, uint256, uint256
    ) {
        DetailedDiagnosis memory d = diagnosisById[_id];
        require(d.id != 0, "Diagnosis ID not found");
        
        return (
            d.id,
            d.condition1, d.confidence1,
            d.condition2, d.confidence2,
            d.condition3, d.confidence3,
            d.doctorDiagnosis,
            d.date,
            d.patientId,
            d.doctorId
        );
    }
    
    // Liste des confidences
    //3 khatir 3 confidences ouu 3 conditions
    function getAllConfidences() public view returns (uint256[] memory) {
        uint256[] memory confs = new uint256[](diagnosisCount * 3);
        
        for (uint i = 0; i < diagnosisCount; i++) {
            uint256 diagId = diagnosisIdsByIndex[i];
            DetailedDiagnosis memory diag = diagnosisById[diagId];
            
            confs[i * 3] = diag.confidence1;
            confs[i * 3 + 1] = diag.confidence2;
            confs[i * 3 + 2] = diag.confidence3;
        }
        
        return confs;
    }

    // Liste des conditions
    function getAllConditions() public view returns (string[] memory) {
        string[] memory conds = new string[](diagnosisCount * 3);
        
        for (uint i = 0; i < diagnosisCount; i++) {
            uint256 diagId = diagnosisIdsByIndex[i];
            DetailedDiagnosis memory diag = diagnosisById[diagId];
            
            conds[i * 3] = diag.condition1;
            conds[i * 3 + 1] = diag.condition2;
            conds[i * 3 + 2] = diag.condition3;
        }
        
        return conds;
    }

    // Liste des IDs de patients
    function getAllPatientIds() public view returns (uint256[] memory) {
        uint256[] memory ids = new uint256[](diagnosisCount);
        
        for (uint i = 0; i < diagnosisCount; i++) {
            uint256 diagId = diagnosisIdsByIndex[i];
            ids[i] = diagnosisById[diagId].patientId;
        }
        
        return ids;
    }

    // Ajouter un élément avec ID auto-incrémenté
    function addElementDiagnosis(
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
        uint256 newId = diagnosisCount + 1;
        
        DetailedDiagnosis memory d = DetailedDiagnosis(
            newId,
            _condition1, _confidence1,
            _condition2, _confidence2,
            _condition3, _confidence3,
            _doctorDiagnosis,
            block.timestamp,
            _patientId,
            _doctorId
        );
        
        diagnosisById[newId] = d;
        diagnosisIdsByIndex[diagnosisCount] = newId;
        diagnosisCount++;
        
        emit DiagnosisAdded(newId, _patientId);
    }

    // Nombre total de diagnostics
    function getDiagnosisCount() public view returns (uint256) {
        return diagnosisCount;
    }
}