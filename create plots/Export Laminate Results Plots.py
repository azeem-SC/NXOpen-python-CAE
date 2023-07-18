## Export Laminate Results plots
## Version: 0.0
## Exports the essential plots of laminate reports based on groups
##
## ---------------------------------------------------------------------------

import math
import NXOpen
import NXOpen.CAE
import NXOpen.UF
import os

def main():
      theSession  = NXOpen.Session.GetSession()
      UFsession = NXOpen.UF.UFSession.GetUFSession()
      listing_window = theSession.ListingWindow
      listing_window.Open()
      workSimPart = theSession.Parts.BaseWork

      
      if not isinstance(workSimPart, NXOpen.CAE.SimPart):
            listing_window.WriteLine("------  " + '\n'+ "ERROR: Work Part Needs to be a .sim")
            return

      listing_window.WriteLine("Working on : " + workSimPart.Name + '\n')
      listing_window.WriteLine("\t.sim file : " + workSimPart.FullPath + '\n' + "---------------------------------------------------------------------------")
      workDirectory = workSimPart.FullPath.replace('.sim','').replace('\\','\\\\').replace(workSimPart.Name, '')
      listing_window.WriteLine("\tDirectory : " + workDirectory + '\n')


      simSimulation = workSimPart.Simulation
      solution = simSimulation.ActiveSolution # gets active solution
      listing_window.WriteLine("Solution Name: " + solution.Name + ', of type ' + str(solution.SolutionType))
      if solution is None:
            listing_window.WriteLine("\nERROR: No active solution found")
            return
      try:
            if "STATIC" not in solution.SolutionType:
                  # checking if the active solution is a static analysis
                  #     if not show warning
                  exit() # exit if ok as its inside the try except block
      except SystemExit:
                  listing_window.WriteLine("\n ---- WARNING ----\nsolution is not Linear Static, its a " 
                        + str(solution.SolutionType))
                  return


      # Getting result object of active solution
      try:
            result = theSession.ResultManager.CreateSolutionResult(solution) #SolutionResult - finds the results of the solution
      except NXOpen.NXException as e:
            listing_window.WriteLine("\nERROR: " + e.GetMessage())
            return
      
      
      # creating folder in work directory for saving plots with name of solution
      plotDirectory = os.path.join(workDirectory, workSimPart.Name + '_' + solution.Name)
      try: 
            if not os.path.exists(plotDirectory):
                  listing_window.WriteLine("Making New Directory to save plots in : " + plotDirectory)
                  os.mkdir(plotDirectory)
      except OSError as error: 
            listing_window.WriteLine("\n ---- WARNING ----\n" + str(error))
            return
      plotDirectoryInside = plotDirectory + '\\\\'     
                                                    
      
      # Getting groups which starts with 'plot'
      plotGroup = findPlotGroups(workSimPart)
      if plotGroup is None:
            listing_window.WriteLine('\nERROR: No Groups found with Names starting with \'plot\'\n\tIdentify Component groups for ploting and rename to start the name with plot')
            return
      else:
            listing_window.WriteLine('\nConsidering Following Groups for Plots:\n')
            for pltGp in plotGroup:
                  listing_window.WriteLine("\t" + pltGp.Name + '\n')

      
      # looping over all load cases and iterations to plot displacement results of FE model
      LCDirectoryInsideList = [] # holds the directory info of each load case
      LCList = []
      for LCs in result.GetLoadcases():
            listing_window.WriteLine("\nLoad Case Name: " + str(LCs.Name) + "\n")
            LCList.append(LCs.Name)
            # makes separate folder for each load cases
            LCDirectory = os.path.join(plotDirectoryInside, LCs.Name)
            try: 
                  if not os.path.exists(LCDirectory):
                        listing_window.WriteLine("\nMaking New Directory to save plots for load cases in : " + LCDirectory)
                        os.mkdir(LCDirectory)
            except OSError as e: 
                  listing_window.WriteLine("\n ---- WARNING ----\n" + str(e))
                  return
            LCDirectoryInside = LCDirectory + '\\\\'
            LCDirectoryInsideList.append(LCDirectoryInside)
            
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
                                    resultComponent = NXOpen.CAE.Result.Component.Magnitude
                                    result_params = CreateResultParams(result,theSession,resultType,resultComponent)
                                    result_access = theSession.ResultManager.CreateResultAccess(result,result_params) # --> NEEDS to be Deleted after processing
                                    postviewID = CreatePostView(theSession, result, result_params, workSimPart)
                                    imageName = solution.Name + '_' + LCs.Name + '_' + 'displacement_Mag'
                                    UFsession.Disp.CreateImage(LCDirectoryInside + imageName, UFsession.Disp.ImageFormat.JPEG, UFsession.Disp.BackgroundColor.WHITE)
                                    #userGroupID = [None] * 1
                                    plotGroupList = [None] * 1
                                    for pltGp in plotGroup:
                                          listing_window.WriteLine('>>>>>>>>>>>' + pltGp.Name + 'of Type  : '+ str(type(pltGp.Name)) + '\n\n')
                                          plotGroupList[0] = pltGp.Name
                                          listing_window.WriteLine('>>>>>>>>>>>TYPE' + str(type(plotGroupList)) + '\tPostViewID: ' + str(postviewID))
                                          #userGroupID = theSession.Post.PostviewGetUserGroupGids(postviewID, plotGroupList) #pltGp.Label
                                          theSession.Post.PostviewApplyUserGroupVisibility(postviewID, [pltGp.Label] , NXOpen.CAE.Post.GroupVisibility.ShowOnly) #theSession.Post.GroupVisibility.ShowOnly
                                          imageName = solution.Name + '_' + LCs.Name + '_' + pltGp.Name +'_displacement_Mag'
                                          UFsession.Disp.CreateImage(LCDirectoryInside + imageName, UFsession.Disp.ImageFormat.JPEG, UFsession.Disp.BackgroundColor.WHITE)
                                    flag = True
                                    break
                        if not flag:
                              listing_window.WriteLine("\nERROR: No Displacement Data Found for Loadcase: "+ LCs.Name + '\n\n')
                              return
                  theSession.ResultManager.DeleteResultAccess(result_access)
                  theSession.ResultManager.DeleteResultParameters(result_params)
                  
            else:
                  listing_window.WriteLine("\n---WARNING---" + '\n' + "more than one iterations found \n - solution might not be static")
                  return            

     
      theSession.Post.PostviewDelete(postviewID)

      # Getting laminate reports of Active Solution
      LamReportOfActiveSol = IsThereLaminateReports(simSimulation,solution)
      if len(LamReportOfActiveSol) == 0:
            # TODO: have to find way to get Laminate reports associated with active solution
            listing_window.WriteLine("\n ---- WARNING ----\nLaminate Report should contain corresponding Solution Name and Loadcase Name (recommend to use the script)")
            return
      else:
            listing_window.WriteLine("\nConsidering following Laminate Post Results\n")
            for LamReport in LamReportOfActiveSol: # for NX 11, each Laminate Report is a LoadCase
                  listing_window.WriteLine('\t' + LamReport.Name + '\n')
                  LCDirectoryInside2 =  getLCDirectory(LamReport, LCDirectoryInsideList, listing_window) # returns the current LC directory
                  listing_window.WriteLine('\t>>>' + str(LCDirectoryInside2) + '\n')
                  for graphicalReports in LamReport.LaminateGraphicalReports:
                        graphicalReportSolResult = theSession.ResultManager.CreateLaminateGraphicalReportResult(graphicalReports) # result of graphical report, its also considered as a solution
                        for graphLC in graphicalReportSolResult.GetLoadcases():
                              for graphIter in graphLC.GetIterations():
                                    # listing_window.WriteLine(('\n>>'+ str(graphIter.Name)))
                                    for LamresultTypes in graphIter.GetResultTypes():
                                          componentList = [0,1,3] # 0-XX, 1-YY, 3-XY
                                          
                                          if (LamresultTypes.UserName == 'Min Stresses - Elemental') or (LamresultTypes.UserName == 'Max Stresses - Elemental'):
                                                listing_window.WriteLine('\n>>>__<<<' + str(LamresultTypes.UserName))
                                                LamResultComponents = LamresultTypes.AskComponents()
                                                # Components are in tuple from class, NXOpen.CAE.Result.ResultComponent
                                                for i in componentList:
                                                      # listing_window.WriteLine('\n>>>__<<<' + str(LamResultComponents[1][i]))
                                                      resultComponent = LamResultComponents[1][i]
                                                      result_params = CreateResultParams(graphicalReportSolResult,theSession,LamresultTypes,resultComponent)
                                                      postviewID = CreatePostView(theSession, graphicalReportSolResult, result_params, workSimPart)
                                                      imageName = str(LamReport.Name.replace('/','_')) + '_' + str(LamResultComponents[0][i]) +'_'+ LamresultTypes.UserName +'_ISO'
                                                      UFsession.Disp.CreateImage(LCDirectoryInside2 + imageName, UFsession.Disp.ImageFormat.JPEG, UFsession.Disp.BackgroundColor.WHITE)

                                                      # Making for each plot group
                                                      userGroupID = [None] * 1
                                                      plotGroupList = [None] * 1
                                                      for pltGp in plotGroup:
                                                            # userGroupID[0] = pltGp.Label
                                                            listing_window.WriteLine('>>>>>>>>>>>' + pltGp.JournalIdentifier + '\n\n')
                                                            plotGroupList[0] = pltGp.JournalIdentifier
                                                            listing_window.WriteLine('>>>>>>>>>>>' + str(plotGroupList[0]))
                                                            userGroupID[0] = theSession.Post.PostviewGetUserGroupGids(postviewID, plotGroupList)
                                                            listing_window.WriteLine('>>>>>>>>>>>' + str(userGroupID[0]))
                                                            theSession.Post.PostviewApplyUserGroupVisibility(postviewID, userGroupID ,NXOpen.CAE.Post.GroupVisibility.ShowOnly)
                                                            imageName = str(LamReport.Name.replace('/','_')) + '_' + str(LamResultComponents[0][i]) + '_' + pltGp.Name + '_'+ LamresultTypes.UserName +'_ISO'
                                                            UFsession.Disp.CreateImage(LCDirectoryInside2 + imageName, UFsession.Disp.ImageFormat.JPEG, UFsession.Disp.BackgroundColor.WHITE)
      theSession.Post.PostviewDelete(postviewID)

      ## ----------------------------------------------------
      ## After Plotting all Results 
      ## ----------------------------------------------------
      
      # Delete solution for cleanup of memory
      theSession.ResultManager.DeleteResult(result)
      # Finally Opens the Folder
      os.startfile(plotDirectory)


def IsThereLaminateReports(simSimulation, solution):
      # Checks if there is laminate reports connected to active solution
      #  and returns the ones
      # Limitation:
      #     This is dependent on name of the laminate report which is not good
      tempCollector = []
      for lamReports in simSimulation.LaminateManager.PostReports:
            if solution.Name.lower() in lamReports.Name.lower():
                  tempCollector.append(lamReports)
      return(tempCollector)

def findPlotGroups(workSimPart):
      # Finds all groups in sim part with Name starts with 'plot'
      tempCollector = []
      for group in workSimPart.CaeGroups:
            if group.Name.lower().startswith("plot"):
                  tempCollector.append(group)
      return(tempCollector)

def CreateResultParams(result, theSession, resultType, resultComponent):
      # Creates result parameters from the loaded result
      result_params = theSession.ResultManager.CreateResultParameters()
      result_params.SetCoordinateSystem(NXOpen.CAE.Result.CoordinateSystem.AbsoluteRectangular)
      result_params.SetGenericResultType(resultType)
      result_params.SetResultComponent(resultComponent)
      
      return result_params
      
def CreatePostView(theSession, solResult, result_params, workSimPart):
      # Creates post view
      postviewID = theSession.Post.CreatePostviewForResult(0, solResult, False, result_params)

      # display change to feature edges, ie hide mesh edges
      primaryEdgeface2 = NXOpen.CAE.Post.EdgeFace()
    
      primaryEdgeface2.EdgeStyle = NXOpen.CAE.Post.EdgeStyle.Feature
      primaryEdgeface2.EdgeColor = workSimPart.Colors.Find("Granite Gray")
      primaryEdgeface2.FaceStyle = NXOpen.CAE.Post.FaceStyle.Opaque
      primaryEdgeface2.FaceColor = workSimPart.Colors.Find("Silver Gray")
      undeformedEdgeface2 = NXOpen.CAE.Post.EdgeFace()
      
      undeformedEdgeface2.EdgeStyle = NXOpen.CAE.Post.EdgeStyle.Feature
      undeformedEdgeface2.EdgeColor = workSimPart.Colors.Find("Granite Gray")
      undeformedEdgeface2.FaceStyle = NXOpen.CAE.Post.FaceStyle.Translucent
      undeformedEdgeface2.FaceColor = workSimPart.Colors.Find("Silver Gray")
      theSession.Post.PostviewSetEdgeFace(postviewID, primaryEdgeface2, undeformedEdgeface2)

      workSimPart.Views.WorkView.Orient("Isometric", NXOpen.View.ScaleAdjustment.Fit)

      theSession.Post.PostviewUpdate(postviewID)

      return postviewID

def getLCDirectory(LamReport, LCDirectoryInsideList, listing_window):
      # returns the directory of the Load case under consideration
      for i in LCDirectoryInsideList:
            if os.path.basename(os.path.dirname(i)).lower() in LamReport.Name.lower():
                  return(i)
            

if __name__ == '__main__':
    main()