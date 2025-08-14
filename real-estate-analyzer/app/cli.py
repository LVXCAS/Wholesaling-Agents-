#!/usr/bin/env python
import typer
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import sys
import os
import csv
from datetime import datetime
from uuid import UUID
import traceback

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

try:
    from app.core.database import get_db, engine
    from app.models.property import Base
    from app.services.property_service import PropertyService
    from app.services.property_analyzer import PropertyAnalyzer
    from app.models.property import PropertyCreate, PropertyTypeEnum
    from app.services.wholesale_analyzer import WholesaleAnalyzer
except ImportError as e:
    print(f"Error importing app modules: {e}")
    sys.exit(1)

app = typer.Typer(name="RealEstateCLI", add_completion=False)
console = Console()

def debug_print(msg: str, data: Any = None) -> None:
    """Helper function to print debug information."""
    console.print(f"[dim]DEBUG: {msg}[/dim]")
    if data:
        console.print(f"[dim]{data}[/dim]")

@app.command()
def init_db():
    """Initialize the database and create all tables."""
    console.print("Initializing database...", style="bold yellow")
    try:
        Base.metadata.create_all(bind=engine)
        console.print("Database initialized successfully!", style="bold green")
    except Exception as e:
        console.print(f"Error initializing database: {e}", style="bold red")
        raise typer.Exit(code=1)

@app.command()
def add_property(
    address: str = typer.Option(..., "--address", help="Property address"),
    city: str = typer.Option(..., "--city", help="City"),
    state: str = typer.Option(..., "--state", help="State"),
    zip_code: str = typer.Option(..., "--zip", help="ZIP code"),
    bedrooms: int = typer.Option(..., "--bedrooms", help="Number of bedrooms"),
    bathrooms: float = typer.Option(..., "--bathrooms", help="Number of bathrooms"),
    sqft: int = typer.Option(..., "--sqft", help="Square footage"),
    property_type: PropertyTypeEnum = typer.Option(PropertyTypeEnum.SINGLE_FAMILY, "--type", help="Property type"),
    lot_size: Optional[float] = typer.Option(None, "--lot-size", help="Lot size in acres"),
    year_built: Optional[int] = typer.Option(None, "--year-built", help="Year built"),
    current_value: Optional[float] = typer.Option(None, "--value", help="Current property value")
):
    """Add a new property to the database."""
    try:
        db = next(get_db())
        service = PropertyService(db)
        
        property_data = PropertyCreate(
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            square_feet=sqft,
            property_type=property_type,
            lot_size=lot_size,
            year_built=year_built,
            current_value=current_value
        )
        
        new_property = service.create_property(property_data)
        console.print(f"✅ Added property: {address}", style="bold green")
        
    except Exception as e:
        console.print(f"Error adding property: {e}", style="bold red")
        raise typer.Exit(code=1)

@app.command()
def show_property(property_id: UUID = typer.Argument(..., help="Property ID")):
    """Show detailed information about a specific property."""
    try:
        db = next(get_db())
        service = PropertyService(db)
        property = service.get_property(property_id)
        
        if not property:
            console.print(f"Property not found: {property_id}", style="bold red")
            raise typer.Exit(code=1)
        
        console.print(f"\n[bold]Property Details: {property.address}[/bold]\n")
        
        table = Table(show_header=False)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("ID", str(property.id))
        table.add_row("Address", property.address)
        table.add_row("City", property.city)
        table.add_row("State", property.state)
        table.add_row("ZIP", property.zip_code)
        table.add_row("Type", property.property_type.value)
        table.add_row("Bedrooms", str(property.bedrooms))
        table.add_row("Bathrooms", str(property.bathrooms))
        table.add_row("Square Feet", str(property.square_feet))
        if property.lot_size:
            table.add_row("Lot Size", f"{property.lot_size} acres")
        if property.year_built:
            table.add_row("Year Built", str(property.year_built))
        if property.current_value:
            table.add_row("Current Value", f"${property.current_value:,.2f}")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"Error retrieving property: {e}", style="bold red")
        raise typer.Exit(code=1)

@app.command()
def analyze_property(
    property_id: Optional[UUID] = typer.Option(None, "--id", help="Property ID"),
    address: Optional[str] = typer.Option(None, "--address", help="Property address")
):
    """Analyze a property by ID or address and calculate ARV."""
    try:
        debug_print("Starting property analysis")
        db = next(get_db())
        service = PropertyService(db)
        analyzer = PropertyAnalyzer(db)
        
        if not property_id and not address:
            console.print("Error: Either --id or --address must be provided", style="bold red")
            raise typer.Exit(code=1)
        
        debug_print(f"Looking up property by {'id' if property_id else 'address'}")
        if address:
            property = service.get_property_by_address(address)
        else:
            property = service.get_property(property_id)
            
        if not property:
            console.print("Property not found", style="bold red")
            raise typer.Exit(code=1)
            
        debug_print("Found property", {
            "id": str(property.id),
            "address": property.address,
            "value": property.current_value
        })
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(description="Finding comparable properties...", total=None)
            try:
                debug_print("Starting analysis")
                result_dict = analyzer.analyze_property(property)
                progress.update(task, completed=True)
                
                debug_print("Analysis complete", result_dict)
                
                console.print("\n[bold]Analysis Results for: [green]{}[/green][/bold]\n".format(property.address))
                
                result_table = Table(show_header=False)
                result_table.add_column("Metric", style="cyan")
                result_table.add_column("Value", style="green")
                
                result_table.add_row("Current Value", f"${property.current_value:,.2f}" if property.current_value else "N/A")
                result_table.add_row("ARV Estimate", f"${result_dict['arv_estimate']:,.2f}")
                result_table.add_row("Confidence Score", f"{result_dict['confidence_score']:.1%}")
                result_table.add_row("Comparable Properties", str(result_dict['comparable_count']))
                if 'repair_estimate' in result_dict:
                    result_table.add_row("Repair Estimate", f"${result_dict['repair_estimate']:,.2f}")
                if 'profit_potential' in result_dict:
                    result_table.add_row("Potential Profit", f"${result_dict['profit_potential']:,.2f}")
                
                console.print(result_table)
                
                if 'calculation_errors' in result_dict and result_dict['calculation_errors']:
                    console.print("\n[bold red]Warnings:[/bold red]")
                    for error in result_dict['calculation_errors']:
                        console.print(f"• {error}", style="yellow")
                        
            except Exception as analysis_error:
                debug_print(f"Analysis error: {str(analysis_error)}")
                debug_print("Traceback", traceback.format_exc())
                raise
        
    except Exception as e:
        console.print(f"Error analyzing property: {e}", style="bold red")
        debug_print("Traceback", traceback.format_exc())
        raise typer.Exit(code=1)

@app.command()
def analyze_all():
    """Analyze all properties in the database."""
    try:
        db = next(get_db())
        service = PropertyService(db)
        analyzer = PropertyAnalyzer(db)
        
        properties = service.list_properties()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            for property in properties:
                task = progress.add_task(f"Analyzing {property.address}...", total=None)
                analysis = analyzer.analyze_property(property)
                progress.update(task, completed=True)
                
        console.print("✅ All properties analyzed successfully!", style="bold green")
        
    except Exception as e:
        console.print(f"Error analyzing properties: {e}", style="bold red")
        raise typer.Exit(code=1)

@app.command()
def export_results(
    format: str = typer.Option("csv", "--format", help="Export format (csv)")
):
    """Export analysis results for all properties."""
    if format.lower() != "csv":
        console.print("Only CSV format is currently supported", style="bold red")
        raise typer.Exit(code=1)
        
    try:
        db = next(get_db())
        service = PropertyService(db)
        analyzer = PropertyAnalyzer(db)
        
        properties = service.list_properties()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_results_{timestamp}.csv"
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'Property ID', 'Address', 'City', 'State',
                'Current Value', 'ARV Estimate', 'Confidence Score',
                'Comparable Count', 'Repair Estimate', 'Profit Potential'
            ])
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                for property in properties:
                    task = progress.add_task(f"Analyzing {property.address}...", total=None)
                    analysis = analyzer.analyze_property(property)
                    
                    writer.writerow([
                        str(property.id),
                        property.address,
                        property.city,
                        property.state,
                        f"${property.current_value:,.2f}" if property.current_value else "N/A",
                        f"${analysis['arv_estimate']:,.2f}",
                        f"{analysis['confidence_score']:.1%}",
                        analysis['comparable_count'],
                        f"${analysis['repair_estimate']:,.2f}" if 'repair_estimate' in analysis else "N/A",
                        f"${analysis['profit_potential']:,.2f}" if 'profit_potential' in analysis else "N/A"
                    ])
                    
                    progress.update(task, completed=True)
        
        console.print(f"✅ Results exported to {filename}", style="bold green")
        
    except Exception as e:
        console.print(f"Error exporting results: {e}", style="bold red")
        debug_print("Traceback", traceback.format_exc())
        raise typer.Exit(code=1)

@app.command()
def list_properties():
    """List all properties in the database."""
    console.print("Listing all properties...", style="bold blue")
    try:
        db_session = next(get_db())
        service = PropertyService(db_session)
        properties = service.list_properties()

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim", width=12)
        table.add_column("Address")
        table.add_column("City")
        table.add_column("Value", justify="right")
        table.add_column("Type")
        table.add_column("Beds", justify="right")
        table.add_column("Baths", justify="right")
        table.add_column("SqFt", justify="right")

        for prop in properties:
            table.add_row(
                str(prop.id)[:8] + "...",
                prop.address,
                prop.city,
                f"${prop.current_value:,.0f}" if prop.current_value else "N/A",
                prop.property_type.value,
                str(prop.bedrooms) if prop.bedrooms else "N/A",
                str(prop.bathrooms) if prop.bathrooms else "N/A",
                str(prop.square_feet) if prop.square_feet else "N/A"
            )

        console.print(table)

    except Exception as e:
        console.print(f"Error listing properties: {e}", style="bold red")
        raise typer.Exit(code=1)

@app.command()
def analyze_wholesale(
    property_id: Optional[UUID] = typer.Option(None, "--id", help="Property ID"),
    address: Optional[str] = typer.Option(None, "--address", help="Property address"),
    condition_score: float = typer.Option(
        0.5,
        "--condition",
        min=0,
        max=1,
        help="Property condition score (0-1, where 1 is excellent)"
    ),
    max_fee_percent: float = typer.Option(
        0.15,
        "--max-fee",
        help="Maximum wholesale fee as percentage of ARV"
    ),
    min_profit: float = typer.Option(
        0.20,
        "--min-profit",
        help="Minimum profit margin for end buyer"
    )
):
    """Analyze a property for wholesaling potential with detailed renovation costs."""
    try:
        debug_print("Starting wholesale analysis")
        db = next(get_db())
        service = PropertyService(db)
        analyzer = WholesaleAnalyzer(db)
        
        if not property_id and not address:
            console.print("Error: Either --id or --address must be provided", style="bold red")
            raise typer.Exit(code=1)
        
        if address:
            property = service.get_property_by_address(address)
        else:
            property = service.get_property(property_id)
            
        if not property:
            console.print("Property not found", style="bold red")
            raise typer.Exit(code=1)
            
        debug_print(f"Analyzing wholesale potential for {property.address}")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(description="Analyzing wholesale potential...", total=None)
            
            analysis = analyzer.analyze_wholesale_deal(
                property,
                condition_score,
                max_fee_percent,
                min_profit
            )
            
            progress.update(task, completed=True)
        
        # Display Results
        console.print(f"\n[bold]Wholesale Analysis for: [green]{property.address}[/green][/bold]\n")
        
        # Property Details Table
        details_table = Table(show_header=False)
        details_table.add_column("Metric", style="cyan")
        details_table.add_column("Value", style="green")
        
        details_table.add_row("Current Value", f"${property.current_value:,.2f}" if property.current_value else "N/A")
        details_table.add_row("ARV Estimate", f"${analysis['arv_analysis']['arv_estimate']:,.2f}")
        details_table.add_row("Deal Score", f"{analysis['deal_metrics']['deal_score']}/100")
        
        console.print(details_table)
        console.print()
        
        # Renovation Analysis Table
        console.print("[bold]Renovation Analysis[/bold]")
        reno_table = Table(show_header=False)
        reno_table.add_column("Item", style="cyan")
        reno_table.add_column("Cost", style="green")
        
        for item, cost in analysis['renovation_analysis']['cost_breakdown'].items():
            reno_table.add_row(item.title(), f"${cost:,.2f}")
            
        reno_table.add_row("Total Renovation Cost", 
                          f"${analysis['renovation_analysis']['total_cost']:,.2f}")
        console.print(reno_table)
        console.print()
        
        # Deal Analysis Table
        console.print("[bold]Deal Analysis[/bold]")
        deal_table = Table(show_header=False)
        deal_table.add_column("Metric", style="cyan")
        deal_table.add_column("Value", style="green")
        
        wholesale = analysis['wholesale_analysis']
        deal_table.add_row("Maximum Allowable Offer", f"${wholesale['maximum_allowable_offer']:,.2f}")
        deal_table.add_row("Current Spread", f"${wholesale['current_spread']:,.2f}")
        deal_table.add_row("Suggested Wholesale Fee", 
                          f"${analysis['recommendations']['suggested_wholesale_fee']['suggested_fee']:,.2f}")
        deal_table.add_row("Estimated Holding Time", 
                          f"{wholesale['estimated_holding_time']:.1f} months")
        deal_table.add_row("Holding Costs", f"${wholesale['holding_costs']:,.2f}")
        deal_table.add_row("Closing Costs", f"${wholesale['closing_costs']:,.2f}")
        deal_table.add_row("Minimum Buyer Profit", f"${wholesale['minimum_buyer_profit']:,.2f}")
        
        console.print(deal_table)
        console.print()
        
        # Recommendations
        console.print("[bold]Recommendations[/bold]")
        console.print(f"Deal Category: [green]{analysis['recommendations']['deal_type']}[/green]")
        console.print("\nSuggested Renovation Scope:")
        for task in analysis['recommendations']['renovation_scope']:
            console.print(f"• {task}")
            
        # Confidence Metrics
        console.print("\n[bold]Confidence Metrics[/bold]")
        conf_table = Table(show_header=False)
        conf_table.add_column("Metric", style="cyan")
        conf_table.add_column("Score", style="green")
        
        metrics = analysis['deal_metrics']['score_components']
        conf_table.add_row("ARV Confidence", f"{metrics['arv_confidence']:.1%}")
        conf_table.add_row("Renovation Confidence", f"{metrics['renovation_confidence']:.1%}")
        conf_table.add_row("Spread Score", f"{metrics['spread_score']:.1%}")
        conf_table.add_row("Condition Score", f"{metrics['condition_score']:.1%}")
        
        console.print(conf_table)
        
    except Exception as e:
        console.print(f"Error analyzing wholesale deal: {e}", style="bold red")
        debug_print("Traceback", traceback.format_exc())
        raise typer.Exit(code=1)

@app.command()
def analyze_wholesale_deal(
    address: str = typer.Option(..., "--address", help="Property address"),
    condition_score: float = typer.Option(0.5, "--condition-score", help="Property condition score (0-1, lower = worse)")
):
    """Analyze a property for wholesaling potential, including renovation and deal scoring."""
    try:
        db = next(get_db())
        from app.services.property_service import PropertyService
        from app.services.wholesale_analyzer import WholesaleAnalyzer
        service = PropertyService(db)
        analyzer = WholesaleAnalyzer(db)
        property = service.get_property_by_address(address)
        if not property:
            console.print(f"Property not found: {address}", style="bold red")
            raise typer.Exit(code=1)
        result = analyzer.analyze_wholesale_deal(property, condition_score)
        console.print(f"\n[bold]Wholesale Deal Analysis for: [green]{property.address}[/green][/bold]\n")
        # ARV
        arv = result['arv_analysis']['arv_estimate']
        confidence = result['arv_analysis']['confidence_score']
        # Renovation
        reno = result['renovation_analysis']['total_cost']
        reno_conf = result['renovation_analysis']['confidence_score']
        # Wholesale
        wholesale = result['wholesale_analysis']
        # Deal
        deal = result['deal_metrics']
        # Recommendations
        rec = result['recommendations']
        table = Table(show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("ARV Estimate", f"${arv:,.2f}")
        table.add_row("ARV Confidence", f"{confidence:.1%}")
        table.add_row("Renovation Cost", f"${reno:,.2f}")
        table.add_row("Renovation Confidence", f"{reno_conf:.1%}")
        table.add_row("Max Allowable Offer (MAO)", f"${wholesale['maximum_allowable_offer']:,.2f}")
        table.add_row("Current Spread", f"${wholesale['current_spread']:,.2f}")
        table.add_row("Max Wholesale Fee", f"${wholesale['max_wholesale_fee']:,.2f}")
        table.add_row("Estimated Holding Time (mo)", str(wholesale['estimated_holding_time']))
        table.add_row("Holding Costs", f"${wholesale['holding_costs']:,.2f}")
        table.add_row("Closing Costs", f"${wholesale['closing_costs']:,.2f}")
        table.add_row("Min Buyer Profit", f"${wholesale['minimum_buyer_profit']:,.2f}")
        table.add_row("Deal Score", f"{deal['deal_score']}/100")
        table.add_row("Deal Type", rec['deal_type'])
        table.add_row("Suggested Wholesale Fee", f"${rec['suggested_wholesale_fee']['suggested_fee']:,.2f}")
        table.add_row("Fee as % of Spread", f"{rec['suggested_wholesale_fee']['fee_as_percent_of_spread']}%")
        table.add_row("Fee as % of ARV", f"{rec['suggested_wholesale_fee']['fee_as_percent_of_arv']}%")
        console.print(table)
        console.print("\n[bold]Renovation Scope:[/bold]")
        for task in rec['renovation_scope']:
            console.print(f"- {task}")
    except Exception as e:
        console.print(f"Error analyzing wholesale deal: {e}", style="bold red")
        import traceback
        traceback.print_exc()
        raise typer.Exit(code=1)

@app.command()
def scan_wholesale_deals(
    min_score: float = typer.Option(
        60.0,
        "--min-score",
        help="Minimum deal score to include (0-100)"
    ),
    condition_threshold: float = typer.Option(
        0.4,
        "--min-condition",
        help="Minimum condition score to consider (0-1)"
    )
):
    """Scan all properties for wholesale opportunities meeting criteria."""
    try:
        db = next(get_db())
        service = PropertyService(db)
        analyzer = WholesaleAnalyzer(db)
        
        properties = service.list_properties()
        
        # Results table
        results_table = Table(
            show_header=True,
            header_style="bold magenta",
            title="Wholesale Opportunities"
        )
        results_table.add_column("Address")
        results_table.add_column("ARV", justify="right")
        results_table.add_column("Deal Score", justify="right")
        results_table.add_column("Spread", justify="right")
        results_table.add_column("Suggested Fee", justify="right")
        results_table.add_column("Category")
        
        opportunities = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            for property in properties:
                task = progress.add_task(
                    description=f"Analyzing {property.address}...",
                    total=None
                )
                
                # Analyze each property
                analysis = analyzer.analyze_wholesale_deal(
                    property,
                    condition_threshold
                )
                
                score = analysis['deal_metrics']['deal_score']
                
                if score >= min_score:
                    opportunities.append({
                        'property': property,
                        'analysis': analysis,
                        'score': score
                    })
                    
                progress.update(task, completed=True)
        
        # Sort opportunities by score
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        # Display results
        for opp in opportunities:
            prop = opp['property']
            analysis = opp['analysis']
            
            results_table.add_row(
                prop.address,
                f"${analysis['arv_analysis']['arv_estimate']:,.0f}",
                f"{opp['score']:.1f}",
                f"${analysis['wholesale_analysis']['current_spread']:,.0f}",
                f"${analysis['recommendations']['suggested_wholesale_fee']['suggested_fee']:,.0f}",
                analysis['recommendations']['deal_type'].split(' - ')[0]
            )
        
        if opportunities:
            console.print(results_table)
            console.print(f"\nFound {len(opportunities)} potential deals!")
        else:
            console.print("\nNo deals found matching criteria.", style="yellow")
        
    except Exception as e:
        console.print(f"Error scanning for wholesale deals: {e}", style="bold red")
        debug_print("Traceback", traceback.format_exc())
        raise typer.Exit(code=1)
