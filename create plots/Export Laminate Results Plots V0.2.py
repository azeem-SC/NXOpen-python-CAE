## Export Laminate Results plots
## Version: 0.1
##    Exports the essential plots of laminate reports based on groups
## Version: 0.2
##    method to get postview user group changed to one using temporary postviewGroup
## ---------------------------------------------------------------------------

import math
import NXOpen
import NXOpen.CAE
import NXOpen.UF
import os
#from typing import List, cast, Tuple

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
     

      ## Getting result object of active solution
      try:
            result = theSession.ResultManager.CreateSolutionResult(solution) #SolutionResult - finds the results of the solution
      except NXOpen.NXException as e:
            listing_window.WriteLine("\nERROR: " + e.GetMessage())
            return
      
      
      ## creating folder in work directory for saving plots with name of solution
      plotDirectory = os.path.join(workDirectory, workSimPart.Name + '_' + solution.Name)
      try: 
            if not os.path.exists(plotDirectory):
                  listing_window.WriteLine("Making New Directory to save plots in : " + plotDirectory)
                  os.mkdir(plotDirectory)
      except OSError as error: 
            listing_window.WriteLine("\n ---- WARNING ----\n" + str(error))
            return
      plotDirectoryInside = plotDirectory + '\\\\'     
                                                    

      ## Getting groups which starts with 'plot'
      plotGroup = findPlotGroups(workSimPart)
      plotGroupNameList = []
      plotGroupNonEmpty = []
      if plotGroup is None:
            listing_window.WriteLine('\nERROR: No Groups found with Names starting with \'plot\'\n\tIdentify Component groups for ploting and rename to start the name with \'plot\'')
            return
      else:
            listing_window.WriteLine('\nConsidering Following Groups for Plots:\n')
            for pltGp in plotGroup:
                  if pltGp.GetEntities() == [] :
                        listing_window.WriteLine('\tWARNING: Group - \'' + pltGp.Name + '\' is Empty,  - Neglected')
                        continue
                  listing_window.WriteLine("\t" + pltGp.Name + '\n')
                  plotGroupNameList.append(pltGp.Name)
                  plotGroupNonEmpty.append(pltGp)

      ## Checking is the sim file is OK for Ploting
      #     because of inability to track postview user group ids the sim file should have following requirements
      #     1 - all groups should be of Elements
      #     2 - groups numbers to be sequential
      try:
            GroupNameList = IsOK4Ploting(workSimPart,simSimulation)
      except NXOpen.NXException as e:
            listing_window.WriteLine(e.GetMessage())
            return
      
      ## Gets the list of cameras in sim
      cameraList = []
      for cam in workSimPart.Cameras:
            # checks if custom view is assigned by giving views same name as plot groups
            if cam.Name in plotGroupNameList:
                  cameraList.append(cam)
                  listing_window.WriteLine('\n[V] Custom views found for Group:' + cam.Name + '\n') # plot group name is same as cam Name
      # cameraList = Collection2List(workSimPart.Cameras)


      ## Trying to track the postview user group IDs
      PostViewUserGpIDList = []
      for pltGp in plotGroupNonEmpty:
            PostViewUserGpIDList.append([GroupNameList.index(pltGp.Name) + 1, pltGp.Name])
      listing_window.WriteLine(str(PostViewUserGpIDList))

      
      ## looping over all load cases and iterations to plot displacement results of FE model
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
                                    userGroupID = [None] * 1                                    
                                    for pltGp in plotGroupNonEmpty:
                                          try:
                                                tempUserGpID = theSession.Post.CreateUserGroupFromEntityLabels(postviewID, 
                                                                  NXOpen.CAE.CaeGroupCollection.EntityType.Element, 
                                                                  MakeElementLabelListFromGroups(pltGp,theSession))
                                                theSession.Post.PostviewApplyUserGroupVisibility(postviewID, [tempUserGpID], NXOpen.CAE.Post.GroupVisibility.ShowOnly)
                                                workSimPart.Views.WorkView.Orient("Isometric", NXOpen.View.ScaleAdjustment.Fit)
                                                if cameraList is None:
                                                      continue
                                                else:
                                                      for cam in cameraList:
                                                            if cam.Name == pltGp.Name:
                                                                  cam.ApplyToView(workSimPart.ModelingViews.WorkView)
                                                workSimPart.ModelingViews.WorkView.Fit()
                                          except NXOpen.NXException as e:
                                                listing_window.WriteLine('ERROR:  ' + e.GetMessage() + '\nTry restarting NX')
                                                return
                                          imageName = solution.Name + '_' + LCs.Name + '_' + pltGp.Name +'_displacement_Mag'
                                          UFsession.Disp.CreateImage(LCDirectoryInside + imageName, UFsession.Disp.ImageFormat.JPEG, UFsession.Disp.BackgroundColor.WHITE)
                                          theSession.Post.UserGroupDelete(result, tempUserGpID) # Deletes the temporary user group
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

     
      # theSession.Post.PostviewDelete(postviewID)
      workSimPart.Views.WorkView.Orient("Isometric", NXOpen.View.ScaleAdjustment.Fit)
      
      return
      # ---------------------------------------------------------------------------------------------------------------------
      # Getting laminate reports of Active Solution
      # ---------------------------------------------------------------------------------------------------------------------
      LamReportOfActiveSol = IsThereLaminateReports(simSimulation,solution)
      if len(LamReportOfActiveSol) == 0:
            # TODO: have to find way to get Laminate reports associated with active solution
            listing_window.WriteLine("\n ---- WARNING ----\nLaminate Report should contain corresponding Solution Name and Loadcase Name (recommend to use the script)")
            return
      else:
            listing_window.WriteLine("\nConsidering following Laminate Post Results\n")
            # PVflagID = 1 # used to increment post view user group IDs
            for LamReport in LamReportOfActiveSol: # for NX 11, each Laminate Report is a LoadCase
                  listing_window.WriteLine('\t' + LamReport.Name + '\n')
                  LCDirectoryInside2 =  getLCDirectory(LamReport, LCDirectoryInsideList, listing_window) # returns the current LC directory
                  #listing_window.WriteLine('\t>>>' + str(LCDirectoryInside2) + '\n')
                  for graphicalReports in LamReport.LaminateGraphicalReports:
                        graphicalReportSolResult = theSession.ResultManager.CreateLaminateGraphicalReportResult(graphicalReports) # result of graphical report, its also considered as a solution
                        for graphLC in graphicalReportSolResult.GetLoadcases():
                              for graphIter in graphLC.GetIterations():
                                    # listing_window.WriteLine(('\n>>'+ str(graphIter.Name)))
                                    for LamresultTypes in graphIter.GetResultTypes():
                                          componentList = [0,1,3] # 0-XX, 1-YY, 3-XY
                                          
                                          if (LamresultTypes.UserName == 'Min Stresses - Elemental') or (LamresultTypes.UserName == 'Max Stresses - Elemental'):
                                                # listing_window.WriteLine('\n>>>__<<<' + str(LamresultTypes.UserName))
                                                LamResultComponents = LamresultTypes.AskComponents()
                                                # Components are in tuple from class, NXOpen.CAE.Result.ResultComponent
                                                for i in componentList:
                                                      # listing_window.WriteLine('\n>>>__<<<' + str(LamResultComponents[1][i]))
                                                      resultComponent = LamResultComponents[1][i]
                                                      result_params = CreateResultParams(graphicalReportSolResult,theSession,LamresultTypes,resultComponent)
                                                      postviewID = CreatePostView(theSession, graphicalReportSolResult, result_params, workSimPart)
                                                      imageName = str(LamReport.Name.replace('/','_')) + '_' + str(LamResultComponents[0][i]) +'_'+ LamresultTypes.UserName
                                                      UFsession.Disp.CreateImage(LCDirectoryInside2 + imageName, UFsession.Disp.ImageFormat.JPEG, UFsession.Disp.BackgroundColor.WHITE)

                                                      # Making for each plot group
                                                      for pltGp in plotGroupNonEmpty:
                                                            try:
                                                                  tempUserGpID = theSession.Post.CreateUserGroupFromEntityLabels(postviewID, 
                                                                                    NXOpen.CAE.CaeGroupCollection.EntityType.Element, 
                                                                                    MakeElementLabelListFromGroups(pltGp,theSession))
                                                                  theSession.Post.PostviewApplyUserGroupVisibility(postviewID, [tempUserGpID] ,NXOpen.CAE.Post.GroupVisibility.ShowOnly)
                                                                  workSimPart.Views.WorkView.Orient("Isometric", NXOpen.View.ScaleAdjustment.Fit)
                                                                  if cameraList is None:
                                                                        continue
                                                                  else:
                                                                        for cam in cameraList:
                                                                              if cam.Name == pltGp.Name:
                                                                                    cam.ApplyToView(workSimPart.ModelingViews.WorkView)
                                                                  workSimPart.ModelingViews.WorkView.Fit()
                                                            except NXOpen.NXException as e:
                                                                  listing_window.WriteLine('ERROR:  ' + e.GetMessage() + '\nTry restarting NX')
                                                                  return
                                                            imageName = str(LamReport.Name.replace('/','_')) + '_' + str(LamResultComponents[0][i]) + '_' + pltGp.Name + '_'+ LamresultTypes.UserName
                                                            UFsession.Disp.CreateImage(LCDirectoryInside2 + imageName, UFsession.Disp.ImageFormat.JPEG, UFsession.Disp.BackgroundColor.WHITE)
                                                            theSession.Post.UserGroupDelete(result, tempUserGpID) # Deletes the temporary user group
                  # PVflagID = PVflagID + 1
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


def IsOK4Ploting(workSimPart,simSimulation):
      # checks is plot groups are OK for ploting
      GroupNameList = []
      # only groups with elements
      for pltGp in workSimPart.CaeGroups:
            GroupNameList.append(pltGp.Name)
            pltGpElements = pltGp.GetEntities()
            for elements in pltGpElements:
                  if not isinstance(elements, NXOpen.CAE.FEElement):
                        raise  NXOpen.NXException("\nERROR:  plot group should be of only Elements\n\tFollowing Group has contents other than Elements (Delete this):\n\t\t" + pltGp.Name)
      
      # >> LATER decided not Needed, as the plot user group numbering depends on opening postviews
      # # Only one simulation
      # solutions = []
      # for sol in simSimulation.Solutions:
      #       solutions.append(sol)
      # if len(solutions) > 1 :
      #       raise NXOpen.NXException("\nERROR: .sim file to have only one solution for ploting")

      return GroupNameList

def Collection2List(collection):
      # converts a collection object to list
      list = []
      for l in collection:
            list.append(l)
      return(list)

def MakeElementLabelListFromGroups(pltGp, theSession):
      # returns list of Element labels of given group
      temp = []
      for elements in pltGp.GetEntities():
            temp.append(elements.Label)
      return(temp)


if __name__ == '__main__':
    main()