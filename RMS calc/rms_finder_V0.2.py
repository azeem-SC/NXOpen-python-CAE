## RMS Finder
##
## version: 0.1 date: March 2023
## Finds RMS displacement of nodes in groups with names starting with 'rms' for all load cases for active simulation
## This tools gets the node numbers from the cae groups (groups in CAE file)
##
## version: 0.2 date: May 2023
## Finds Csys with name which starts 'acs' and asks for user input to enter outof plane direction
##
## Limitations:
##    - as the node numbers are read from sim file (groups in sim file), not result, if nodes are renumbered, then node numbers in result odb will be different to numbers in post processer
##      this has to be checked
##    - won't work if remeshed
## Future :
##    - selecting CSYS to check results
##    - RMS in one axis of the selected CSYS
##----------------------------------------------------

import NXOpen
import NXOpen.CAE
import NXOpen.UF

def main() : 
      theSession = NXOpen.Session.GetSession()
      theUI = NXOpen.UI.GetUI()
      theUfSession  = NXOpen.UF.UFSession.GetUFSession()
      listing_window = theSession.ListingWindow
      listing_window.Open()

      work_part = theSession.Parts.BaseWork
      listing_window.WriteLine("Working on sim file : " + work_part.Name + '\n' + "---------------------------------------------------------------------------")
      # listing_window.WriteLine("Note:\n\tRMS will be with respect to absolute CSYS and will be on displacement magnitude \n")
      listing_window.WriteLine("Note:\t")
      listing_window.WriteLine("\tMake sure that node numbering of result file and current .fem file is same \n-------------------------------------------")
      if not isinstance(work_part, NXOpen.CAE.SimPart):
            listing_window.WriteLine("------  " + '\n'+ "ERROR: Work Part Needs to be a .sim")
            return
      solution = work_part.Simulation.ActiveSolution # gets active solution

      if "STATIC" not in solution.SolutionType:
            listing_window.WriteLine("\n ---- WARNING ----\nsolution is not Linear Static")
            return

      listing_window.WriteLine("Solution Name: " + solution.Name)

      if solution is None:
            listing_window.WriteLine("No active solution found")
            return
    

      try:
            result = theSession.ResultManager.CreateSolutionResult(solution) #SolutionResult - finds the results of the solution
      except NXOpen.NXException as e:
            listing_window.WriteLine("\nERROR: " + e.GetMessage())
            return

      # finding groups with name starting with 'rms' - for solution groups
      # ie for groups in model tree
      rms_group_names = []
      listing_window.WriteLine("  finding RMS for nodes in following groups: ")
      for group in work_part.CaeGroups:
            if group.Name.lower().startswith("rms"):
                  rms_group_names.append(group.Name)
                  listing_window.WriteLine("\t\t\t" + group.Name + '\n')
      

      if not rms_group_names:
            listing_window.WriteLine("\nERROR: No groups found with names starting with 'rms'")
            return

      ## Finding csys with name starting with 'rms'
      ACS = []
      for csys in work_part.CoordinateSystems:
            if csys.Name.lower().startswith('acs'):
                  ACS.append(csys)

           
      if len(ACS)>1:
            listing_window.WriteLine('\nWARNING: More than one csys with name starting with acs found \n')
            listing_window.WriteLine('\nCsys considered as ACS:\t\t')
            outofPlaneDir = []
            matchedGrpList = []
            for sys in ACS:
                  listing_window.WriteLine('\t\t' + sys.Name)
                  theUI.LockAccess()
                  outofPlaneDir_temp,l,retVar = theUfSession.Ui.AskStringInput('ddd', 'X')
                  outofPlaneDir.append(outofPlaneDir_temp)
                  theUI.UnlockAccess()
                  # Matching csys and group names
                  for gps in  rms_group_names:
                        if sys.Name.lower().replace('acs','') in gps:
                          matchedGrpList.append(gps)    
                  listing_window.WriteLine(str(matchedGrpList))
      elif len(ACS) == 1:
            listing_window.WriteLine('Csys considered as ACS:\t' + ACS[0].Name + '\n')
            theUI.LockAccess()
            outofPlaneDir,l,retVar = theUfSession.Ui.AskStringInput('ddd', 'X')
            theUI.UnlockAccess()
            listing_window.WriteLine('\nOut of plane direction for csys named ' + ACS[0].Name + ' is ' + outofPlaneDir +'\n')
      elif not ACS:
            listing_window.WriteLine('\nWARNING: No Csys found with name starting with ACS, neglecting all\n')

      # Doing for Absolute Csys and Magnitude of displacement
      listing_window.WriteLine('\n\n=================================================================\n')
      listing_window.WriteLine('\t\twith respect to Absolute Csys and Magnitude')
      listing_window.WriteLine('=================================================================\n')
      getRMS4LCs(listing_window, result, rms_group_names,work_part, theSession, None, None)

      # checks if user entered correct component
      for temp in outofPlaneDir:
            if temp.lower() not in ['x','y','z']:
                  listing_window.WriteLine('\n Out of plane direction entered is InValid')
                  return

      if ACS:
            # Doing for matched Csys
            listing_window.WriteLine('\n\n=================================================================\n')
            listing_window.WriteLine('\t\tWith respect to User Input')
            listing_window.WriteLine('=================================================================\n')
            if not matchedGrpList:
                  listing_window.WriteLine('WARNING: No Matching Group Found, Group name to contain Csys Name\n')
                  return
            else:
                  listing_window.WriteLine('\t'+ 'Group' + '\t\t' + 'User Csys' + '\t\t' + 'Out of Plane Direction' + '\n')
                  listing_window.WriteLine('-------------------------------------------------------------------------------')
                  for i, (acs,dir,mGpLst) in enumerate(zip(ACS,outofPlaneDir,matchedGrpList)):
                        listing_window.WriteLine('\n---------------------------------------------------')
                        listing_window.WriteLine('\t' + mGpLst + '\t\t' + acs.Name + '\t\t' + dir)
                        # Doing for user Input Values
                        listing_window.WriteLine('---------------------------------------------------')
                        getRMS4LCs(listing_window, result, mGpLst, work_part, theSession, dir, acs)     
      


def getRMS4LCs(listing_window, result, rms_group_names,work_part, theSession, component, CoordianteSYS):
      # finding for all LCs
      if component is None:
            # None - Magnitude
            component_outplane = NXOpen.CAE.Result.Component.Magnitude
      elif component.lower() == 'x':
            component_outplane = NXOpen.CAE.Result.Component.X
      elif component.lower() == 'y':
            component_outplane = NXOpen.CAE.Result.Component.Y
      elif component.lower() == 'z':
            component_outplane = NXOpen.CAE.Result.Component.Z
      else:
            listing_window.WriteLine('ERROR: Out of plane Component entered is invalid')
            return

      if CoordianteSYS is None:
            # None - absolute rectangular
            CoordianteSYS_m = NXOpen.CAE.Result.CoordinateSystem.AbsoluteRectangular
            source = NXOpen.CAE.Result.CoordinateSystemSource.NotSet
            id = -1
      else:
            CoordianteSYS_m = NXOpen.CAE.Result.CoordinateSystem.SelectRectangular
            source = NXOpen.CAE.Result.CoordinateSystemSource.Model
            id = CoordianteSYS.Label
      
      for LCs in result.GetLoadcases():
            listing_window.WriteLine("\nLoad Case Name: " + str(LCs.Name) + "\n")
            result_params = theSession.ResultManager.CreateResultParameters()
            if len(result.AskIterations(LCs.Label - 1)) == 1:
                  # checks if there is more than one iterations in a load case, if so it might be a 
                  # frequency run or response, might not be static analysis
                  # RMS result valid only for static runs
                  for iter in LCs.GetIterations():
                        flag = False
                        for resultType in iter.GetResultTypes():
                              # finding all result types in this particular iteration
                              if resultType.Quantity == NXOpen.CAE.Result.Quantity.Displacement :
                                    # Getting the displacement result type alone
                                    DisplacementData = resultType
                                    result_params.SetGenericResultType(DisplacementData)
                                    result_params.SetResultComponent(component_outplane)
                                    result_params.SetCoordinateSystem(CoordianteSYS_m)
                                    result_params.SetSelectedCoordinateSystem(source, id)
                                    result_access = theSession.ResultManager.CreateResultAccess(result, result_params) # --> NEEDS to be Deleted after processing
                                    flag = True
                                    break
                        if not flag:
                              listing_window.WriteLine("\nERROR: No Displacement Data Found" + '\n\n')
                              break
                  
                  ## Finding RMS of current load case for all groups that starts with 'rms'
                  if isinstance(rms_group_names, list):
                        for group_name in rms_group_names:
                              listing_window.WriteLine("\tGroup: " + group_name)
                              try:
                                    rms_disp = get_rms_disp(group_name, result_access, work_part, listing_window, result)
                              except ValueError as e:
                                    return
                              if rms_disp is not None:
                                    listing_window.WriteLine("\t\tRMS displacement of nodes : " + str(round(rms_disp[0],4)))
                                    listing_window.WriteLine("\t\tPTV of nodes : " + str(round(rms_disp[1],4)))
                              else:
                                    listing_window.WriteLine("\tUnable to calculate RMS displacement for group " + group_name + "in load case " + LCs.Name)
                                    listing_window.WriteLine("")
                  else:
                        listing_window.WriteLine("\tGroup: " + rms_group_names)
                        try:
                              rms_disp = get_rms_disp(rms_group_names, result_access, work_part, listing_window, result)
                        except ValueError as e:
                              return
                        if rms_disp is not None:
                              listing_window.WriteLine("\t\tRMS displacement of nodes : " + str(round(rms_disp[0],4)))
                              listing_window.WriteLine("\t\tPTV of nodes : " + str(round(rms_disp[1],4)))
                        else:
                              listing_window.WriteLine("\tUnable to calculate RMS displacement for group " + rms_group_names + "in load case " + LCs.Name)
                              listing_window.WriteLine("")

                  theSession.ResultManager.DeleteResultAccess(result_access)
                  theSession.ResultManager.DeleteResultParameters(result_params)
                  
            else:
                  listing_window.WriteLine("\n---WARNING---" + '\n' + "more than one iterations found \n - solution might not be static")
                  return


def get_rms_disp(group_name, result_access, WorkPart, listing_window,result):
    rms_group = WorkPart.CaeGroups.FindObject(group_name)
    rms_disp = 0.0
    if rms_group is None:
        return None

    rms_nodes = rms_group.GetEntities()

    if not rms_nodes:
      listing_window.WriteLine("\nERROR: No nodes found in group: " + rms_group.Name)
      return None

    max = 0 # holder for finding PTV
    min = 0 # holder for finding PTV
    for node in rms_nodes:
            node_index = result.AskNodeIndex(node.Label) # checks node index of nodes in result file (.op2), label is the node number that we see, index for machine, goes from 0 to #ofnodes
            if not isinstance(node, NXOpen.CAE.FENode):
                  listing_window.WriteLine("\nERROR: rms group should be of only nodes")
                  return None   
            try:
                  disp = result_access.AskNodalResult(node_index)
            except NXOpen.NXException as e:
                  listing_window.WriteLine('\n\tERROR:' + e.GetMessage())
                  listing_window.WriteLine('\n\tPossible reason: Node numbering of result file (OP2) different compared to work sim part')
                  raise ValueError(e)
            if disp<min:
                  min = disp
            if disp>max:
                  max = disp
            rms_disp += disp**2  # Sum the square of the magnitude-displacement of each node
    rms_disp /= len(rms_nodes)  # Divide by the number of nodes
    rms_disp = rms_disp**0.5  # Take the square root to get the RMS displacement

    return rms_disp, (max-min)
    
if __name__ == '__main__':
    main()