## RMS Finder
## version: 0.1 date: March 2023
## Finds RMS displacement of nodes in groups with names starting with 'rms' for all load cases for active simulation
## This tools gets the node numbers from the cae groups (groups in CAE file)
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

def main() : 
      theSession = NXOpen.Session.GetSession()
      listing_window = theSession.ListingWindow
      listing_window.Open()

      work_part = theSession.Parts.BaseWork
      listing_window.WriteLine("Working on sim file : " + work_part.Name + '\n' + "---------------------------------------------------------------------------")
      listing_window.WriteLine("Note:\n\tRMS will be with respect to absolute CSYS and will be on displacement magnitude \n")
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
                                    result_params.SetResultComponent(NXOpen.CAE.Result.Component.Magnitude)
                                    result_access = theSession.ResultManager.CreateResultAccess(result, result_params) # --> NEEDS to be Deleted after processing
                                    flag = True
                                    break
                        if not flag:
                              listing_window.WriteLine("\nERROR: No Displacement Data Found" + '\n\n')
                              break
                  
                  ## Finding RMS of current load case for all groups that starts with 'rms'
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