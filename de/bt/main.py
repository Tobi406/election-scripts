import glob
import os
import sys
import re
import json
from bs4 import BeautifulSoup
import math
import statistics

os.chdir(r'D:\\wahlscripts\\de\\bt') # change working dir to current dir

def removeNaN(number):
  if number == "n/a":
    return 0
  return number

def gNameModification(gName):
  if (gName == "GR\u00dcNE"):
    return "GR\u00dcNE/B 90"
  return gName

def sainteLague(results: dict, totalSeats: int, optionalPercent: int, directMandates: dict = {}):
  modifier = 0.0000001
  modifierModifier = 1

  adjusted = {}
  allVotes = 0
  allSeats = 0
  for k, v in results.items():
    allVotes = allVotes + int(v)
  while (allSeats != totalSeats):
    for k, v in results.items():
      value = round(
        int(v)
        /
        (
          (allVotes/totalSeats)*optionalPercent
        )
      )
      if (directMandates != {} and k in directMandates):
        directMandateCount = directMandates[k]
        if (value < directMandateCount):
          value = directMandateCount
      adjusted[k] = value
    allSeats = 0
    for k, v in adjusted.items():
      allSeats = allSeats + int(v)
    if (allSeats < totalSeats):
      optionalPercent = optionalPercent - modifier
    if (allSeats > totalSeats):
      optionalPercent = optionalPercent + modifier
    #print(f"{optionalPercent} {str(allSeats)} should be {str(totalSeats)} {adjusted}")
    #sys.stdout.write(f"\r{optionalPercent} {str(allSeats)} should be  {str(totalSeats)} {adjusted}")
    #sys.stdout.flush()
  #print("\n")

  return adjusted

def getStatesSeats():
  f = open('_population.json', "r")
  population = json.load(f)
  seats = sainteLague(population, 598, 1)

  return seats

def getStateLists(consideredParties: list):
  fstrings = glob.glob("data/erg1_*.xml")
  fadjusted = [] # Contains newest files
  for fstring in fstrings:
    regex = re.search(r"^(.+0)(.)\.xml", fstring)
    before = regex.group(1)
    number = regex.group(2)
    # check if there exists a file with any higher number
    readyToPass = True
    for i in range(int(number) + 1, 10):
      if fstrings.__contains__(before + str(i) + ".xml"):
        readyToPass = False
    if (readyToPass):
      fadjusted.append(fstring)
  
  totalResults = {}

  for fstring in fadjusted:
    f = open(fstring, "r", encoding="utf-8")
    soup = BeautifulSoup(f, "xml")
    results = soup.find_all("Gebietsergebnis")
    for result in results:
      if (result['Gebietsart'] == "LAND"):
        groupResults = result.find_all('Gruppenergebnis')
        for groupResult in groupResults:
          if (groupResult['Gruppenart'] == "PARTEI"):
            voteResults = groupResult.find_all('Stimmergebnis')
            for voteResult in voteResults:
              if (voteResult['Stimmart'] == "LISTE"):
                lNumber = result['Gebietsnummer']
                gName = gNameModification(groupResult['Name'])
                votes = voteResult['Anzahl']
                # Only calculate for considered parties
                if not (consideredParties.__contains__(gName)):
                  continue

                if not (lNumber in totalResults):
                  totalResults[lNumber] = {}
                totalResults[lNumber][gName] = removeNaN(votes)

  return totalResults

def getDirectMandates():
  fstrings = glob.glob("data/erg3_*.xml")
  fadjusted = [] # Contains newest files
  for fstring in fstrings:
    regex = re.search(r"^(.+0)(.)\.xml", fstring)
    before = regex.group(1)
    number = regex.group(2)
    # check if there exists a file with any higher number
    readyToPass = True
    for i in range(int(number) + 1, 10):
      if fstrings.__contains__(before + str(i) + ".xml"):
        readyToPass = False
    if (readyToPass):
      fadjusted.append(fstring)

  totalResults = {}

  for fstring in fadjusted:
    f = open(fstring, "r", encoding="utf-8")
    soup = BeautifulSoup(f, "xml")
    results = soup.find_all("Gebietsergebnis")
    for result in results:
      if (result['Gebietsart'] == "WAHLKREIS"): # Get Wahlkreis, not Land or Bund
        groupResults = result.find_all('Gruppenergebnis')
        for groupResult in groupResults: 
          if (groupResult['Gruppenart'] == "PARTEI"): # Get all results for parties
            voteResults = groupResult.find_all('Stimmergebnis')
            for voteResult in voteResults:
              if (voteResult['Stimmart'] == "DIREKT"): # Get all direct votes
                lNumber = result['UegGebietsnummer']
                wkNumber = result['Gebietsnummer']
                gName = gNameModification(groupResult['Name'])
                votes = voteResult['Anzahl']
                if not (lNumber in totalResults):
                  totalResults[lNumber] = {}
                if not (wkNumber in totalResults[lNumber]):
                  totalResults[lNumber][wkNumber] = {}
                totalResults[lNumber][wkNumber][gName] = votes

  def getWinner(value):
    winner = list(
        reversed(
          sorted(
            value.items(),
            key=lambda x: int(
              removeNaN(x[1])
            )
          )
        )
      )[0][0] # first 0 standing for (partyName, votes) and second standing for partyName
    return winner

  def calculateTogether(wks: dict):
    lResults = {}
    for v in wks.values():
      if not (v in lResults):
        lResults[v] = 1
      else:
        lResults[v] = lResults[v] + 1
    return lResults

  totalResults = {k: {k2: getWinner(v2) for k2, v2 in v.items()} for k, v in totalResults.items()}
  totalResults = {k: calculateTogether(v) for k, v in totalResults.items()}
  return totalResults

def stateToFederal(toFederal: dict):
  trParty = {}
  for ls in toFederal.values():
    for party, partySeats in ls.items():
      if not (party in trParty):
        trParty[party] = partySeats
      else:
        trParty[party] = trParty[party] + partySeats 
  return trParty

def getFederalResults(prop):
  federalFile = "erg0_0009905.xml"
  f = open("data/" + federalFile, "r", encoding="utf-8")
  soup = BeautifulSoup(f, "xml")
  result = soup.find_all('Gebietsergebnis')[0]
  groupResults = result.find_all('Gruppenergebnis')

  percentageResults = {}
  for groupResult in groupResults:
    if (groupResult['Gruppenart'] == "PARTEI"):
      voteResults = groupResult.find_all('Stimmergebnis')
      for voteResult in voteResults:
        if (voteResult['Stimmart'] == "LISTE"):
          gName = gNameModification(groupResult['Name'])
          vote = removeNaN(voteResult[prop])
          percentageResults[gName] = vote
  
  return percentageResults

def getConsideredParties(directMandates: dict, percentageResults: dict):
  # Constants
  nationalMinorityParties = ['SSW']
  hurdlePercent = 5
  hurdleConstituencies = 3

  parties = []
  for k, v in percentageResults.items():
    if (
      float(v) >= float(hurdlePercent) or
      nationalMinorityParties.__contains__(k) or
      (k in directMandates and directMandates[k] >= hurdleConstituencies)
    ):
      parties.append(k)

  return parties

def assignListSeats(stateSeats: dict, stateLists: dict):
  totalResults = {}

  for stateId, stateSeatNumber in stateSeats.items():
    totalResults[stateId] = sainteLague(stateLists[stateId], stateSeatNumber, 1)

  return totalResults
  
def getMinimumSeatsCount(directMandates: dict, assignedListSeats: dict):
  totalResults = {}

  for state, stateSeats in assignedListSeats.items():
    for partyName, listSeats in stateSeats.items():
      if not (partyName in directMandates[state]):
        directMandates[state][partyName] = 0
      if not (partyName in assignedListSeats[state]):
        assignedListSeats[state][partyName] = 0
      directMandateCount = directMandates[state][partyName]
      assignedListCount = assignedListSeats[state][partyName]
      mediumSeatsCount = math.ceil(statistics.mean([directMandateCount, assignedListCount]))
      
      seatsCount = 0

      if not (state in totalResults):
        totalResults[state] = {}

      if (directMandateCount >= assignedListCount):
        seatsCount = directMandateCount
      if (directMandateCount < assignedListCount):
        seatsCount = mediumSeatsCount

      totalResults[state][partyName] = seatsCount
  
  return totalResults

def getProportionalContingent(lagueResults: dict, contingentMinimumSeats: dict, seatsNumber):
  expandSeats = False
  proportionalSeats = sainteLague( lagueResults, seatsNumber, 1)
  for k, v in proportionalSeats.items():
    if (v < contingentMinimumSeats[k]):
      expandSeats = True
  if (expandSeats):
    return getProportionalContingent(lagueResults, contingentMinimumSeats, seatsNumber + 1)
  else:
    return proportionalSeats

def getEndcontingent(lagueResults: dict, directMandates: dict, seatsNumber):
  ignoredOverhang = 3

  expandSeats = False
  overhang = {}
  endSeats = sainteLague(lagueResults, seatsNumber, 1)
  for k, v in endSeats.items():
    directPartyMandates = directMandates[k]
    if (v < directPartyMandates):
      if not (k in overhang):
        overhang[k] = 0
      overhang[k] = overhang[k] + (directPartyMandates - v)
  if (sum(overhang.values()) > ignoredOverhang):
    expandSeats = True
  if (expandSeats):
    return getEndcontingent(lagueResults, directMandates, seatsNumber + 1)
  else:
    for k, v in overhang.items():
      endSeats[k] = endSeats[k] + v
    return endSeats

def getEndcontingentStates(endContingent: dict, stateLists: dict, directMandates: dict):
  apportionHelper = {}
  totalResults = {}

  for state, values in stateLists.items():
    for party, votes in values.items():
      if not (party in apportionHelper):
        apportionHelper[party] = {}
      if not ("votes" in apportionHelper[party]):
        apportionHelper[party]["votes"] = {}
      apportionHelper[party]["votes"][state] = int(votes)
  for state, values in directMandates.items():
    for party, directMandateCount in values.items():
      if not (party in apportionHelper):
        apportionHelper[party] = {}
      if not ("direct" in apportionHelper[party]):
        apportionHelper[party]["direct"] = {}
      apportionHelper[party]["direct"][state] = directMandateCount

  for party, totalSeats in endContingent.items():
    totalResults[party] = sainteLague(apportionHelper[party]["votes"], totalSeats, 1, apportionHelper[party]["direct"])

  return totalResults

def onlyConsidered(toOnlyConsider: dict, consideredParties: list):
  modified = {}
  for k, v in toOnlyConsider.items():
    if (consideredParties.__contains__(k)):
      modified[k] = v
  
  return modified

def jsonDump(d: dict):
  return json.dumps(d, sort_keys=True, indent=4)

directMandates = getDirectMandates()
consideredParties = getConsideredParties(stateToFederal(directMandates), getFederalResults('Prozent'))
consideredVotes = onlyConsidered(getFederalResults('Anzahl'), consideredParties)

stateSeats = getStatesSeats()
stateLists = getStateLists(consideredParties)

assignedListSeats = assignListSeats(stateSeats, stateLists)

directMandateMinimumSeats = stateToFederal( getMinimumSeatsCount(directMandates, assignedListSeats) )
proportionalMinimumSeats = sainteLague(consideredVotes, 598, 1)
contingentMinimumSeats = stateToFederal(assignedListSeats)

proportionalContingent = getProportionalContingent(consideredVotes, contingentMinimumSeats, 598)

endContingent = getEndcontingent(consideredVotes, stateToFederal(directMandates), sum(proportionalContingent.values()))
endContingentStates = getEndcontingentStates(endContingent, stateLists, directMandates)

print("End contingent states:", endContingentStates)
print("By states:", stateToFederal(endContingentStates), sum(stateToFederal(endContingentStates).values()))

print("Proportional:", proportionalMinimumSeats, sum(proportionalMinimumSeats.values()))
print("Contingent:", contingentMinimumSeats, sum(contingentMinimumSeats.values()))
print("Direct mandates:", directMandateMinimumSeats, sum(directMandateMinimumSeats.values()))
print("Proportional results:", proportionalContingent, sum(proportionalContingent.values()))

print("End contingent:", endContingent, sum(endContingent.values()))

print("Considered parties:", consideredParties)
