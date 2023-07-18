## Batch Laminate Report Maker
## version: 0.1
## Makes multiple Laminate Reports for all load cases in active simulation
## 
## ---------------------------------------------------------------------------------------------------

import math
import NXOpen
import NXOpen.CAE
def main() : 

    theSession  = NXOpen.Session.GetSession()
    listing_window = theSession.ListingWindow
    listing_window.Open()
    workSimPart = theSession.Parts.BaseWork

    listing_window.WriteLine("working on sim file : " + workSimPart.Name + '\n' + "---------------------------------------------------------------------------")
    
    if not isinstance(workSimPart, NXOpen.CAE.SimPart):
      listing_window.WriteLine("------  " + '\n\n'+ "   Work Part Needs to be a .sim")
      exit()

    simSimulation = workSimPart.Simulation
    simSolution = simSimulation.ActiveSolution
   
    if simSolution is None:
      listing_window.WriteLine("No active solution found")
      exit()

    try:
      if "STATIC" not in simSolution.SolutionType:
            # checking if the active solution is a static analysis
            #     if not show warning
            exit()
    except SystemExit:
            listing_window.WriteLine("\n ---- WARNING ----\n\t> solution is not static")
            exit()

    listing_window.WriteLine("/*/*//*/**//*//*/*/*/*/*/*/")
    listing_window.WriteLine("Solution Name: " + simSolution.Name)
    result = theSession.ResultManager.CreateSolutionResult(simSolution) #SolutionResult - finds the results of the solution
    
    
    
    
    for LCs in result.GetLoadcases():
      if len(result.AskIterations(LCs.Label - 1)) == 1:
                  # checks if there is more than one iterations in a load case, if so it might be a 
                  # frequency run or response, might not be static analysis
                  # this tool is to make laminate report for multiple LCs
                  for iter in LCs.GetIterations():
                        laminatePostReportBuilder1 = workSimPart.Simulation.LaminateManager.PostReports.CreateLaminatePostReportBuilder(NXOpen.CAE.LaminatePostReport.Null)
                        listing_window.WriteLine( "Laminate Report_" + simSolution.Name + "_" + LCs.Name)
                        laminatePostReportBuilder1.Name = "Laminate Report_" + simSolution.Name + "_" + LCs.Name
                        solutionnames2 = [None] * 1 
                        solutionnames2[0] = simSolution.Name
                        selectallsubcases2 = [None] * 1 
                        selectallsubcases2[0] = False
                        loadcasenames2 = [None] * 1 
                        loadcasenames2[0] = LCs.Name
                        iterationnames2 = [None] * 1 
                        iterationnames2[0] = iter.Name
                        laminatePostReportBuilder1.SetSelectedSolutions(solutionnames2, selectallsubcases2, loadcasenames2, iterationnames2)
                  laminatePostReportBuilder1.Commit()
                  laminatePostReportBuilder1.Destroy()
      else:
            listing_window.WriteLine("\n\n--WARNING--\n\t There are more than one Iteration, means loadcase might not be Linear static solution")

    
    

    
    
    
    
    
    
    
    
    #laminatePostReport1 = nXObject1
    #simSolution.LaminateManager.PostReports.ActivePostReport = laminatePostReport1

    for lamReports in simSimulation.LaminateManager.PostReports:
      listing_window.WriteLine("\n>>>  " + str(lamReports.Name))
      simSimulation.LaminateManager.PostReports.ActivePostReport = lamReports
      laminateGraphicalReportBuilder1 = simSimulation.LaminateManager.PostReports.CreateLaminateGraphicalReportBuilder(NXOpen.CAE.LaminateGraphicalReport.Null)
      selectElementsBuilder1 = laminateGraphicalReportBuilder1.ElementFilter.SelectElements
      selectTaggedObjectList1 = selectElementsBuilder1.Selection
    
      laminateGraphicalReportBuilder1.Name = "Graphical_" + lamReports.Name
    
      laminateGraphicalReportBuilder1.SolverInput = NXOpen.CAE.LaminateGraphicalReportBuilder.SolverInputType.SolverPlyStressesAndStrains
    
      laminateGraphicalReportBuilder1.PlyMiddle = True
    
      laminateGraphicalReportBuilder1.PlyStress = True
    
      laminateGraphicalReportBuilder1.PlyStrainRule = NXOpen.CAE.LaminateGraphicalReportBuilder.EnvelopeRule.AbsMax
    
      laminateGraphicalReportBuilder1.FailureIndexRule = NXOpen.CAE.LaminateGraphicalReportBuilder.EnvelopeRule.AbsMax
    
      laminateGraphicalReportBuilder1.StrengthRatioRule = NXOpen.CAE.LaminateGraphicalReportBuilder.EnvelopeRule.AbsMin
    
      laminateGraphicalReportBuilder1.SafetyMarginRule = NXOpen.CAE.LaminateGraphicalReportBuilder.EnvelopeRule.Min
    
      laminateGraphicalReportBuilder1.SafetyFactor = 1.0
    
      laminateGraphicalReportBuilder1.PlyExportOption = NXOpen.CAE.LaminateGraphicalReportBuilder.PlyExportOptionType.Layer
    
      laminateGraphicalReportBuilder1.ElementFilter.SelectAllElements = True
    
      laminateGraphicalReportBuilder1.PlyFilter.SelectAllPlies = True
       
      nXObject2 = laminateGraphicalReportBuilder1.Commit()

      laminateGraphicalReportBuilder1.Destroy()
    
      laminateGraphicalReport1 = nXObject2
      laminateGraphicalReport1.GenerateResults()

    
    
    
#     ----------------------------------------------
#       Dialog Begin Graphical Report
#     ----------------------------------------------
    
    
    
    
    
    

    
    
    
#     ----------------------------------------------
#       Menu: Tools->Journal->Stop Recording
#     ----------------------------------------------
    
if __name__ == '__main__':
    main()