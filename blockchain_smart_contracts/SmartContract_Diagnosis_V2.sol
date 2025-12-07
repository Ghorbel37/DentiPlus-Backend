// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.8.6 <0.9.0;

/**
 * @title Storage
 * @dev Store & retrieve value in a variable
 * @custom:dev-run-script ./scripts/deploy_with_ethers.ts
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

    // Stockage on-chain des diagnostics détaillés
    DetailedDiagnosis[] public diagnoses;
    // Liste des diagnostics off-chain (hashs)
    OffChainDiagnosis[] public offChainHashes;

    // mapping par id donné par l'utilisateu
    mapping(uint256 => DetailedDiagnosis) public diagnosisById;
     // Stockage off-chain par patient ID
    mapping(uint256 => OffChainDiagnosis) public offChainDiagnoses;

  // Événement pour signaler l'enregistrement off-chain
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
         // Optionnel : vérifier que l'id n'existe pas déjà sinon fct s'arrete 
        for (uint i = 0; i < diagnoses.length; i++) {
            require(diagnoses[i].id != _id, "Diagnosis ID already exists");
        }
         // push pour ajouter un nouvel element au tab
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
        diagnoses.push(d);
        diagnosisById[_id] = d;
        emit DiagnosisAdded(_id, _patientId);
    }

    //  Lier avec le backend via hash (off-chain data)
    function storeDiagnosisHash(uint256 patientId, string memory diagnosisHash) public {
        require(bytes(diagnosisHash).length > 0, "Hash is required");
        offChainDiagnoses[patientId] = OffChainDiagnosis(diagnosisHash, block.timestamp, patientId, 0);
    }

    // Récupérer le hash d’un diagnostic off-chain
    function getDiagnosisHash(uint256 patientId) public view returns (string memory, uint256) {
        OffChainDiagnosis memory d = offChainDiagnoses[patientId];
        return (d.hash, d.timestamp);
    }

// Récupérer les hash off-chain par l'ID du diagnostic
    function getHashesById(uint256 _diagnosisId) public view returns (string[] memory) {
        uint256 count = 0;
        // Première boucle pour compter combien de hash sont liés à ce diagnosisId
        for (uint i = 0; i < offChainHashes.length; i++) {
            if (offChainHashes[i].diagnosisId == _diagnosisId) {
                count++;
            }
        }


         // Création du tableau résultat
        string[] memory hashes = new string[](count);
        uint256 index = 0;

          // Deuxième boucle pour remplir le tableau
        for (uint i = 0; i < offChainHashes.length; i++) {
            if (offChainHashes[i].diagnosisId == _diagnosisId) {
                hashes[index] = offChainHashes[i].hash;
                index++;
            }
        }

        return hashes;
    }

     // Enregistrer un hash off-chain lié à un diagnostic
    function addOffChainHashByDiagnosisId(string memory _hash, uint256 _diagnosisId) public {
        require(bytes(_hash).length > 0, "Hash is required");

        // Chercher le diagnostic pour récupérer le patientId
        uint256 patientId = 0;
        bool found = false;

        for (uint i = 0; i < diagnoses.length; i++) {
            if (diagnoses[i].id == _diagnosisId) {
                patientId = diagnoses[i].patientId;
                found = true;
                break;
            }
        }

        require(found, "Diagnosis ID not found");

        offChainHashes.push(OffChainDiagnosis(_hash, block.timestamp, patientId, _diagnosisId));
        emit HashAdded(_hash, patientId, _diagnosisId, block.timestamp);
    }

        //  Récupérer un diagnostic on-chain par id

    function getDiagnosisId(uint256 _id) public view returns (
        uint256,
        string memory, uint256,
        string memory, uint256,
        string memory, uint256,
        string memory, uint256, uint256, uint256
    ) {//si nal9aw diag bil id yali correspond _id retourne immediatement ou stockiwih fi variable d 
        for (uint i = 0; i < diagnoses.length; i++) {
            if (diagnoses[i].id == _id) {
                DetailedDiagnosis memory d = diagnoses[i];
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
        }
        // Si aucun diagnostic n'est trouvé, on lève une erreur
        revert("Diagnosis ID not found");
    }

  // Liste des confidences // il *3 hekom khatir aandik 3 confiance 
    function getAllConfidences() public view returns (uint256[] memory) {
        uint256[] memory confs = new uint256[](diagnoses.length * 3);
        for (uint i = 0; i < diagnoses.length; i++) {
            confs[i * 3] = diagnoses[i].confidence1;
            confs[i * 3 + 1] = diagnoses[i].confidence2;
            confs[i * 3 + 2] = diagnoses[i].confidence3;
        }
        return confs;
    }

   // Liste des conditions
    function getAllConditions() public view returns (string[] memory) {
        string[] memory conds = new string[](diagnoses.length * 3);
        for (uint i = 0; i < diagnoses.length; i++) {
            conds[i * 3] = diagnoses[i].condition1;
            conds[i * 3 + 1] = diagnoses[i].condition2;
            conds[i * 3 + 2] = diagnoses[i].condition3;
        }
        return conds;
    }

// Liste des IDs de patients
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
        uint256 _patientId,
        uint256 _doctorId
    ) public {
        uint256 newId = diagnoses.length + 1;
        diagnoses.push(DetailedDiagnosis(
            newId,
            _condition1, _confidence1,
            _condition2, _confidence2,
            _condition3, _confidence3,
            _doctorDiagnosis,
            block.timestamp,
            _patientId,
            _doctorId
        ));
    }

  // Nombre total de diagnostics
    function getDiagnosisCount() public view returns (uint) {
        return diagnoses.length;
    }
}
