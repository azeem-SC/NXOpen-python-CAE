import math
import NXOpen
import NXOpen.CAE
def main() : 

    theSession  = NXOpen.Session.GetSession()
    workFemPart = theSession.Parts.BaseWork
    listing_window = theSession.ListingWindow
    listing_window.Open()
    for laminate in workFemPart.PhysicalPropertyTables:
      if isinstance(laminate,NXOpen.CAE.Laminate):
            listing_window.WriteLine('Name:' + laminate.Name)


if __name__ == '__main__':
    main()