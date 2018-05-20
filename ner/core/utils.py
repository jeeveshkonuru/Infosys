import spacy
from spacy.gold import GoldParse
import random
import os
import shutil
import _pickle as p
import redis
import uuid

nlp = spacy.load('en')
r = redis.StrictRedis(host='localhost', port=6379, db=0)

def entities(text, list_labels):
    """
    Returns the entities in a given piece of text fragment
    """
    text = text.replace("\n", " ")
    text = " ".join(text.split())
    entity_list = []
    for entries in nlp(text).sents:
        sentence = entries.text
        for entity in nlp(sentence).ents:
            entity_dict = {}
            entity_dict["start"] = entries.start + entity.start
            entity_dict["end"] = entries.start + entity.end
            entity_dict["entity"] = entity.text
            entity_dict["type"] = entity.label_
            if entity_dict["type"] in list_labels:
                entity_list.append(entity_dict)
    return entity_list

def entitiesCustom(modelID, text, list_labels):
    """
    Uses the custom model modelID to parse the given text fragment 'text' and returns entities with their types

    :param modelID: identifier of the model to be used for parsing text
    :param text: text fragmented from where the entities are extracted
    :param list_labels: list of allowed types of labels to be extraced from the given text
    :return: List containing entities along with their types
    """

    os.system('pip install ner/core/Models/{}.tar.gz'.format(modelID))

    customModel = __import__("en_"+modelID)
    custom_nlp = customModel.load()
    text = text.replace("\n", " ")
    text = " ".join(text.split())
    entity_list = []
    for entries in custom_nlp(text).sents:
        sentence = entries.text
        for entity in custom_nlp(sentence).ents:
            entity_dict = {}
            entity_dict["start"] = entries.start + entity.start
            entity_dict["end"] = entries.start + entity.end
            entity_dict["entity"] = entity.text
            entity_dict["type"] = entity.label_
            if entity_dict["type"] in list_labels:
                entity_list.append(entity_dict)

    os.system('pip uninstall --yes {}'.format('en_'+modelID))
    return entity_list

def ParseDataFile(filename):
    """
    Parses the given input file and returns it in a format that can be directly fed into Spacy for training
    :param filename: filename
    :return: List of sentences with entity offsets in each sentence
    """
    file = open(filename, 'r', encoding='utf8')
    trainDataset = []
    sentence = []
    entOffSets = []
    sentLen = 0
    prevType = ''
    start = 0
    end = 0
    for ind, line in enumerate(file):
        print(ind, line)
        text = line.strip().split()
        if 'DOCSTART' in line or 'docstart' in line:
            continue

        if line.strip() == '':
            if start != end:
                entOffSets.append((start, end, prevType))
            if len(sentence) != 0:
                trainDataset.append((' '.join(sentence), [x for x in entOffSets]))
            del sentence[:]
            del entOffSets[:]
            sentLen = 0
            start = 0
            end = 0
            prevType = ''
            # if len(trainDataset) > 100:
            #     break
            continue

        # print('TEXT', text[-1], start, end)
        if text[-1] != 'O':
            label = text[-1].split('-')
            if label[0] == 'I':# and (prevType!='' or prevType==label[1]):
                if prevType == '':
                    start = sentLen
                    end = start + len(text[0])
                    prevType = label[1]

                elif prevType == label[1]:
                    end = end + len(text[0]) + 1

                elif start != end:
                    entOffSets.append((start, end, prevType))
                    start = end + 1
                    end = start + len(text[0])
                    prevType = label[1]

            elif start != end:
                entOffSets.append((start, end, prevType))
                start = end + 1
                end = start + len(text[0])
                prevType = label[1]


        else:
            # if the current token is not an entity
            if start!=end:
                # print('ADDING', start, end)
                entOffSets.append((start, end, prevType))
                start = 0
                end = 0
                prevType = ''

        sentence.append(text[0])
        sentLen += len(text[0]) + 1

    return trainDataset

def trainModel(nlp, training_datasetID, isNewModel, labels=None):
    """
    Trains a custom Spacy model and returns the trained instance of English()
    :param training_datasetID: ID of the dataset to be used for training the spacy model
    :param labels: list of allowed types of entities
    :return: Object of type English() after training
    """
    # nlp = spacy.load('en')
    if labels is not None:
        for label in labels:
            nlp.entity.add_label(label)

    # train_data = ParseDataFile(os.path.join(os.getcwd(),'core\\TrainingDataset\\' + training_datasetID))
    train_data = p.load(open('ner/core/TrainingDataset/{}'.format(training_datasetID), 'rb'))

    # Add new words to vocab
    for raw_text, _ in train_data:
        doc = nlp.make_doc(raw_text)
        for word in doc:
            _ = nlp.vocab[word.orth]

    for itn in range(5):
        print('TRAINING', itn)
        random.shuffle(train_data)
        ind = 1
        for raw_text, entity_offsets in train_data:
            # if labels is not None:
            #     flag = False
            #     for e in entity_offsets:
            #         if e[2] not in labels:
            #             flag = True
            #     if flag:
            #         continue
            if isNewModel:
                flag = False
                for e in entity_offsets:
                    if e[2] not in labels:
                        flag = True
                if flag:
                    continue
            print('{} out of {}'.format(ind, len(train_data)), raw_text, entity_offsets)
            ind += 1
            doc = nlp.make_doc(raw_text)
            gold = GoldParse(doc, entities=entity_offsets)
            nlp.tagger(doc)
            # print('done-1')
            loss = nlp.entity.update(doc, gold)
            print('Done')
            if ind>100:
                break
            # while(True):
            #     continue
    nlp.end_training()

    return nlp

def generateJSON(modelID):
    file = open('ner/core/'+modelID+'.json', 'w')
    file.write('{"name": "'+modelID+'","lang": "en","version": "1.0.0","spacy_version": ">=1.7.0,<2.0.0","description": "Custom Model for Spacy NER","author": "Rohit Naik Jarupla","url": "","url":"http:cse.iitd.ac.in/cs1140224","email": "cs1140224@iitd.ac.in","license": "CC BY-SA 3.0"}')
    file.flush()
    file.close()

def buildModel(training_datasetID, labels):
    nlp = spacy.load('en')
    nlp = trainModel(nlp=nlp, training_datasetID=training_datasetID, isNewModel=True, labels=labels)
    modelID = str(uuid.uuid1())
    nlp.save_to_directory(os.path.join(os.getcwd(), 'ner/core/'+modelID))
    generateJSON(modelID)
    os.chdir('ner/core')
    os.system('mkdir custom_model')
    # TODO: Throws error when connected to infosys network
    os.system('python -m spacy package --meta {}.json {} custom_model'.format(modelID, modelID))
    os.chdir('custom_model/en_{}-1.0.0/'.format(modelID))
    os.system('python setup.py sdist')
    os.chdir('../../')
    # os.system('dir')
    os.system('move custom_model\\en_{}-1.0.0\\dist\\en_{}-1.0.0.tar.gz Models\\{}.tar.gz'.format(modelID, modelID, modelID))
    shutil.rmtree('custom_model')
    shutil.rmtree(modelID)
    os.remove(modelID+'.json')
    os.chdir('../../')
    return modelID

# def delTrainingDataset(training_datasetID):
#     os.remove('core\\TrainingDataset\\{}'.format(training_datasetID))

def updateModel(existing_modelID, training_datasetID, duplicate, labels=None):
    os.system('pip install ner/core/Models/{}.tar.gz'.format(existing_modelID))

    customModel = __import__("en_"+existing_modelID)
    custom_nlp = customModel.load()

    nlp = trainModel(custom_nlp, training_datasetID, False, labels)

    if duplicate:
        modelID = str(uuid.uuid1())
    else:
        modelID = existing_modelID
    nlp.save_to_directory(os.path.join(os.getcwd(), 'ner/core/' + modelID))
    generateJSON(modelID)
    os.chdir('ner/core')
    os.system('mkdir custom_model')
    os.system('python -m spacy package --meta {}.json {} custom_model'.format(modelID, modelID))
    os.chdir('custom_model/en_{}-1.0.0/'.format(modelID))
    os.system('python setup.py sdist')
    os.chdir('../../')
    # os.system('dir')
    if duplicate is not True:
        os.remove('Models\\{}.tar.gz'.format(existing_modelID))
    os.system(
        'move custom_model\\en_{}-1.0.0\\dist\\en_{}-1.0.0.tar.gz Models\\{}.tar.gz'.format(modelID, modelID, modelID))
    shutil.rmtree('custom_model')
    shutil.rmtree(modelID)
    os.remove(modelID + '.json')
    os.chdir('../../')
    return modelID

    os.system('pip uninstall --yes {}'.format('en_'+existing_modelID))

def parseReplace(filepath):
    data = ParseDataFile(filepath)
    os.remove(filepath)
    p.dump(data, open(filepath, 'wb'))

def returnMetrics(nlp, datasetID, list_labels, isExactMatch):
    data = p.load(open('ner/core/TestingDataset/{}'.format(datasetID), 'rb'))

    TP = {}; FN = {}; FP = {}; entityListFound = {}; entityListGiven = {}
    for label in list_labels:
        TP[label] = 0
        FN[label] = 0
        FP[label] = 0
        entityListFound[label] = []
        entityListGiven[label] = []

    for raw_text, offsets in data:
        ents = nlp(raw_text).ents
        for entity in ents:
            if entity.label_ in list_labels:
                entityListFound[entity.label_].append(entity.text)

        for entity in offsets:
            if entity[2] in list_labels:
                entityListGiven[entity[2]].append(raw_text[entity[0]:entity[1]])

        for entityType, entities in entityListFound.items():
            for ind, eachEnt in enumerate(entities):
                if isExactMatch:
                    if eachEnt in entityListGiven[entityType]:
                        del entityListGiven[entityType][entityListGiven[entityType].index(eachEnt)]
                        del entityListFound[entityType][ind]
                        TP[entityType] += 1
                else:
                    for ind2, entGiven in enumerate(entityListGiven[entityType]):
                        temp = eachEnt.strip().split()
                        flag = False
                        for t in temp:
                            if t in entGiven.strip().split():
                                del entityListGiven[entityType][ind2]
                                # print(eachEnt, entGiven, ind, entityListFound[entityType], entityListFound[entityType][ind])
                                del entityListFound[entityType][ind]
                                TP[entityType] += 1
                                flag = True
                                break
                        if flag:
                            break

            FP[entityType] += len(entityListFound[entityType])
            FN[entityType] += len(entityListGiven[entityType])

        for label in list_labels:
            entityListFound[label] = []
            entityListGiven[label] = []

    entityScores = []
    for label in list_labels:
        entityScore = {}
        entityScore['entity'] = label
        entityScore['true_positive'] = TP[label]
        entityScore['false_positive'] = FP[label]
        entityScore['false_negative'] = FN[label]
        if (TP[label] + FN[label])!=0:
            entityScore['recall'] = TP[label] / (TP[label] + FN[label])
        else:
            entityScore['recall'] = 0
        if (TP[label] + FP[label])!=0:
            entityScore['precision'] = TP[label] / (TP[label] + FP[label])
        else:
            entityScore['precision'] = 0
        if entityScore['recall'] !=0 and entityScore['precision'] !=0:
            entityScore['f1-score'] = 2 / ((1 / entityScore['recall']) + (1 / entityScore['precision']))
        else:
            entityScore['f1-score'] = 0
        entityScores.append(entityScore)
        print(entityScore)

    return entityScores

def defaultMetrics(testing_datasetID, list_labels, isExactMatch):
    return returnMetrics(nlp=nlp, datasetID=testing_datasetID, list_labels=list_labels, isExactMatch=isExactMatch)

def customMetrics(modelID, testing_datasetID, list_labels, isExactMatch):
    os.system('pip install ner/core/Models/{}.tar.gz'.format(modelID))

    customModel = __import__("en_" + modelID)
    custom_nlp = customModel.load()

    metrics = returnMetrics(nlp=custom_nlp, datasetID=testing_datasetID, list_labels=list_labels, isExactMatch=isExactMatch)

    os.system('pip uninstall --yes {}'.format('en_' + modelID))

    return metrics