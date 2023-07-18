import math
import NXOpen
import NXOpen.CAE
def main() : 

    theSession  = NXOpen.Session.GetSession()
    workFemPart = theSession.Parts.BaseWork

    
    listing_window = theSession.ListingWindow
    listing_window.Open()

    #check if fem or afem
    if(isinstance(workFemPart,NXOpen.CAE.FemPart) or isinstance(workFemPart,NXOpen.CAE.AssyFemPart)): 
      pass
    else:
      listing_window.WriteLine('\n Error: Please make fem or afem as work part')
      return

    listing_window.WriteLine('\n\n\t------------------- Materials Used -------------------\n\n')
    coreMatList = []
    coreMatNameList = []
    for material in workFemPart.MaterialManager.PhysicalMaterials:
      if IsItCoreMaterial(material):
            listing_window.WriteLine('\t'+ material.Name+ '\t\tCore Material')
            coreMatList.append(material)
            coreMatNameList.append(material.Name)
      else:
            listing_window.WriteLine('\t'+ material.Name+ '\t\tNot Core Material')
    
    if not coreMatList:
      listing_window.WriteLine('\nError: No Core material found with 1000 as ratio of transverse and inplane properties of material') 
      return
    
    listing_window.WriteLine('\n\t------------------------------------------------------\n\t------------------------------------------------------\n\t') 

    coreIDTable = []
    coreID = 5000
    for coreMat in coreMatList:
      coreID = coreID + 1
      coreIDTable.append([coreMat.Name, coreID])

    materialNameList = []
    propertywithCoreMat = []
    for laminate in workFemPart.PhysicalPropertyTables:
      if isinstance(laminate,NXOpen.CAE.Laminate):
            for ply in laminate.PlyGroups: # Laminate grp collection
                  for ply1 in ply.Plies: # laminate ply collection
                        materialNameList.append(ply1.GetMaterialName())
                        if ply1.GetMaterialName() in coreMatNameList:
                              propertywithCoreMat.append(laminate)
                              for mat in coreIDTable:
                                    if ply1.GetMaterialName() == mat[0]:
                                          ply1.GlobalId = mat[1]

    listing_window.WriteLine('\n\t------------ Properties with core Material -----------\n\t ')
    res = []
    [res.append(x) for x in propertywithCoreMat if x not in res]
    propertywithCoreMat = res
    for ppty in propertywithCoreMat:
      listing_window.WriteLine('\t' + ppty.Name + '\n')

    listing_window.WriteLine('\n\t------------------------------------------------------\n\t------------------------------------------------------\n\t')


    listing_window.WriteLine('\n\t-------------- Ply ID and Core Materials -------------\n\n')

    for IDlist in coreIDTable:
      listing_window.WriteLine('\t' + str(IDlist[0]) + '\t\t' + str(IDlist[1]))

    listing_window.WriteLine('\n\t------------------------------------------------------\n\t------------------------------------------------------\n\t')

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