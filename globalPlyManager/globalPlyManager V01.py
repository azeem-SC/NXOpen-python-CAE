import math
import NXOpen
import NXOpen.CAE
def main() : 

    theSession  = NXOpen.Session.GetSession()
    workFemPart = theSession.Parts.BaseWork

    
    listing_window = theSession.ListingWindow
    listing_window.Open()

    #check if fem or afem
    if(isinstance(workFemPart,NXOpen.CAE.FemPart)):
            try:
                  # coreMatList , coreMatNameList = getFEMCoreMaterials(workFemPart)
                  # coreIDTable = generateGlobalplyIDTable(coreMatList)
                  # propertywithCoreMat = getpptyWithCoreMat(workFemPart, coreIDTable, coreMatNameList)
                  coreMatList , coreMatNameList, coreIDTable, propertywithCoreMat = doIDManageInFEM(workFemPart)
            except  NXOpen.NXException as e:
                  listing_window.WriteLine(e.GetMessage())
                  return

    elif(isinstance(workFemPart,NXOpen.CAE.AssyFemPart)):
            try:
                  coreMatList , coreMatNameList, coreIDTable, propertywithCoreMat =  doIDManageInAFEM(workFemPart)

            except  NXOpen.NXException as e:
                  listing_window.WriteLine(e.GetMessage(    ))
                  return
      
    else:
            listing_window.WriteLine('\n Error: Please make fem or afem as work part')
            return
       
    if not coreMatList:
            listing_window.WriteLine('\nError: No Core material found with 1000 as ratio of transverse and inplane properties of material') 
            return
    
    listing_window.WriteLine('\n\n\t-------------- Core Materials Identified -------------\n\n')
    for coreMat in coreMatNameList:
            listing_window.WriteLine('\t' + coreMat)
    listing_window.WriteLine('\n\t------------------------------------------------------\n\t------------------------------------------------------\n\t') 
    
    listing_window.WriteLine('\n\t------------ Properties with core Material -----------\n\t ')

    if not propertywithCoreMat:
            listing_window.WriteLine('\t ERROR: No Properties Found with above core materials')
            return
    else:
            for ppty in propertywithCoreMat:
                  listing_window.WriteLine('\t' + ppty.Name + '\n')


    listing_window.WriteLine('\n\t------------------------------------------------------\n\t------------------------------------------------------\n\t')


    listing_window.WriteLine('\n\t-------------- Ply ID and Core Materials -------------\n\n')

    for IDlist in coreIDTable:
            listing_window.WriteLine('\t' + str(IDlist[0]) + '\t\t' + str(IDlist[1]))

    listing_window.WriteLine('\n\t------------------------------------------------------\n\t------------------------------------------------------\n\t')

def getFEMCoreMaterials(workFemPart):
      # get core materials used in fem
      coreMatList = []
      coreMatNameList = []
      for material in workFemPart.MaterialManager.PhysicalMaterials:
            if IsItCoreMaterial(material):
                  # theSession  = NXOpen.Session.GetSession()
                  # listing_window = theSession.ListingWindow
                  # listing_window.Open()
                  # listing_window.WriteLine('\t'+ material.Name+ '\t\tCore Material')
                  coreMatList.append(material)
                  coreMatNameList.append(material.Name)
      try:
            if not coreMatList:            
                  raise NXOpen.NXException
      except NXOpen.NXException:
            pass
      # else:
      # removing duplicates
      coreMatList = removeDUplicates(coreMatList)
      coreMatNameList = removeDUplicates(coreMatNameList)
      return(coreMatList,coreMatNameList)

def doIDManageInAFEM(workAFemPart, coreMatList_afem = [], coreMatNameList_afem = [], coreIDTable_afem = [], propertywithCoreMat_afem = []):
      # get core materials used in afem
      theSession = NXOpen.Session.GetSession()
      listing_window = theSession.ListingWindow
      listing_window.Open()
      listing_window.WriteLine('-- open -- ')
      if not propertywithCoreMat_afem:
            listing_window.WriteLine('Initiating list as Empty')      
      else:
            listing_window.WriteLine('Initiating list with Content')      

           
      if isinstance(workAFemPart,NXOpen.CAE.AssyFemPart):
            listing_window.WriteLine('AFEM  - ' + workAFemPart.Name + '\n')
            coreMatList_afem_C = []
            coreMatNameList_afem_C = []
            coreIDTable_afem_C = []
            propertywithCoreMat_afem_C =[]
            for child in workAFemPart.BaseFEModel.GetChildren():
                  try:
                        listing_window.WriteLine('recursion loop  - ' + child.Prototype.OwningPart.Name + '\t\n:::')
                        for i in propertywithCoreMat_afem:
                              listing_window.WriteLine('*****' + i.Name)
                  except:
                        pass
                  coreMatList_afem, coreMatNameList_afem, coreIDTable_afem, propertywithCoreMat_afem = doIDManageInAFEM(child.Prototype.OwningPart)
                  coreMatList_afem_C = coreMatList_afem_C + coreMatList_afem
                  coreMatNameList_afem_C = coreMatNameList_afem_C + coreMatNameList_afem
                  coreIDTable_afem_C = coreIDTable_afem_C + coreIDTable_afem
                  propertywithCoreMat_afem_C = propertywithCoreMat_afem_C + propertywithCoreMat_afem

            return(
            removeDUplicates(coreMatList_afem_C),
            removeDUplicates(coreMatNameList_afem_C),
            removeDUplicates(coreIDTable_afem_C),
            propertywithCoreMat_afem_C
            )

      elif isinstance(workAFemPart,NXOpen.CAE.FemPart):
            listing_window.WriteLine('\tFEM  - ' + workAFemPart.Name + '\n')
            try:
                  a,b,c,d = doIDManageInFEM(workAFemPart)
                  coreMatList_afem = coreMatList_afem + a
                  coreMatNameList_afem = coreMatNameList_afem + b
                  coreIDTable_afem = coreIDTable_afem + c
                  
                  for i in propertywithCoreMat_afem:
                        listing_window.WriteLine('\n\t>>>  Klee - d- -----' + i.Name)
                  propertywithCoreMat_afem = propertywithCoreMat_afem + d
                  for i in propertywithCoreMat_afem:
                        listing_window.WriteLine('\n\t>>>  klaa - d- -----' + i.Name)
            except NXOpen.NXException as e:
                  raise e
            # finally:
      # remove duplicates inside fem not in AFEM
      # if not isinstance(workAFemPart,NXOpen.CAE.AssyFemPart):
      #       # theSession  = NXOpen.Session.GetSession()
      #       # listing_window = theSession.ListingWindow
      #       # listing_window.Open()
      #       # listing_window.WriteLine('\t>>before\t' + str(workAFemPart))
      #       # listing_window.WriteLine('\t>>before\t'+ str(coreMatList_afem[0].Name))

      #       coreMatList_afem = removeDUplicates(coreMatList_afem)
      #       coreMatNameList_afem = removeDUplicates(coreMatNameList_afem)
      #       coreIDTable_afem = removeDUplicates(coreIDTable_afem)
      #       propertywithCoreMat_afem = removeDUplicates(propertywithCoreMat_afem)
      #       listing_window.WriteLine('\t>>after\t'+ str(coreMatList_afem[0].Name))

            return(
                  coreMatList_afem,
                  coreMatNameList_afem,
                  coreIDTable_afem,
                  propertywithCoreMat_afem
            )
      
      

def doIDManageInFEM(workFemPart):
      coreMatList , coreMatNameList = getFEMCoreMaterials(workFemPart)
      theSession  = NXOpen.Session.GetSession()
      listing_window = theSession.ListingWindow
      listing_window.Open()
      listing_window.WriteLine('\n\t\t>>>2--' + workFemPart.Name)
      listing_window.WriteLine('\t\t' + coreMatNameList[0])
      coreIDTable = generateGlobalplyIDTable(coreMatList)
      propertywithCoreMat = getpptyWithCoreMat(workFemPart, coreIDTable, coreMatNameList)
      return(coreMatList , coreMatNameList, coreIDTable, propertywithCoreMat)


def getpptyWithCoreMat(workFemPart,coreIDTable,coreMatNameList):
    propertywithCoreMat = []
    for laminate in workFemPart.PhysicalPropertyTables:
      if isinstance(laminate,NXOpen.CAE.Laminate):
            for ply in laminate.PlyGroups: # Laminate grp collection
                  for ply1 in ply.Plies: # laminate ply collection
                        if ply1.GetMaterialName() in coreMatNameList:
                              propertywithCoreMat.append(laminate)
                              for mat in coreIDTable:
                                    if ply1.GetMaterialName() == mat[0]:
                                          ply1.GlobalId = mat[1]
                                          ply1.Description = 'Core Ply'
    res = []
    [res.append(x) for x in propertywithCoreMat if x not in res]
    propertywithCoreMat = res
    return(propertywithCoreMat)

def removeDUplicates(list):
      res = []
      [res.append(x) for x in list if x not in res]
      return(res)

def IsItCoreMaterial(material):
      # checks if its core material
      MatPPTY = material.GetPropTable()
      thresh = 1000
      G23byE1 = MatPPTY.GetDoublePropertyValue('ShearModulus3') / MatPPTY.GetDoublePropertyValue('YoungsModulus')
      G13byE1 = MatPPTY.GetDoublePropertyValue('ShearModulus2') / MatPPTY.GetDoublePropertyValue('YoungsModulus')
      G23byE2 = MatPPTY.GetDoublePropertyValue('ShearModulus3') / MatPPTY.GetDoublePropertyValue('YoungsModulus2')
      G13byE2 = MatPPTY.GetDoublePropertyValue('ShearModulus2') / MatPPTY.GetDoublePropertyValue('YoungsModulus2')

      if all(x > thresh for x in [G23byE1, G13byE1 ,G23byE2, G13byE2]):
            return(True)

def generateGlobalplyIDTable(coreMatList):
      # generate core global ply ID table for each core material
      coreIDTable = []
      coreID = 5000
      for coreMat in coreMatList:
            coreID = coreID + 1
            coreIDTable.append([coreMat.Name, coreID])
      return(coreIDTable)

# YoungsModulus
# YoungsModulus2
# YoungsModulus3
# YoungsModulusTXTg
# YoungsModulusTXTg2
# YoungsModulusTXTg3
# YoungsModulusTX
# PoissonsRatioType
# PoissonsRatioControl
# PoissonsRatio
# PoissonsRatio2
# PoissonsRatio3
# PoissonsRatioTXTg
# PoissonsRatioTXTg2
# PoissonsRatioTXTg3
# PoissonsRatioTempDoc
# ShearModulus
# ShearModulus2
# ShearModulus3




if __name__ == '__main__':
    main()