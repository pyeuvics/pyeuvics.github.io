"""Overview structure is validated without duplicating upstream calculations."""
import json
from pathlib import Path
import pytest
from tests.support.overview import overview_contract,write_overview_candidate
from tools.site_assembly.overview_data import validate_overview,OverviewFigureError,JSON_PATH,CSV_PATH,SVG_PATH
from tools.site_assembly.structured import finite_number,StructuredInputError


@pytest.mark.parametrize('damage',['root','missing-version','wrong-version','package-name','files','status','recoil-number','harmonic-bool','grid','infinite-setting','missing-model-field','empty-limitation'])
def test_descriptor_failures_are_typed(damage: str,tmp_path: Path) -> None:
    write_overview_candidate(tmp_path);path=tmp_path/JSON_PATH;value=json.loads(path.read_text(encoding='utf-8'))
    if damage=='root':value=[]
    elif damage=='missing-version':del value['package']['version']
    elif damage=='wrong-version':value['package']['version']='9.9.9'
    elif damage=='package-name':value['package']['name']='different'
    elif damage=='files':value['files']=['kinetic-energy-scan.csv','other.svg']
    elif damage=='status':value['artifact_status']='validated'
    elif damage=='recoil-number':value['model']['recoil_included']=1
    elif damage=='harmonic-bool':value['model']['harmonic']=True
    elif damage=='grid':value['model']['electron_kinetic_energy_MeV']['point_count']=60
    elif damage=='infinite-setting':value['model']['laser_wavelength_nm']=float('inf')
    elif damage=='missing-model-field':del value['model']['polarization']
    else:value['limitations'][0]=' '
    path.write_text(json.dumps(value),encoding='utf-8')
    with pytest.raises(OverviewFigureError):validate_overview(overview_contract(tmp_path))


@pytest.mark.parametrize(('column','replacement'),[(0,'nan'),(1,'nan'),(1,'inf'),(1,'-1'),(1,'0'),(0,'2.2')])
def test_nonphysical_or_unreviewed_csv_values_fail(column: int,replacement: str,tmp_path: Path) -> None:
    write_overview_candidate(tmp_path);path=tmp_path/CSV_PATH;rows=path.read_text(encoding='utf-8').splitlines()
    values=rows[10].split(',');values[column]=replacement;rows[10]=','.join(values)
    path.write_text('\n'.join(rows)+'\n',encoding='utf-8')
    with pytest.raises(OverviewFigureError):validate_overview(overview_contract(tmp_path))


@pytest.mark.parametrize('damage',['header','row-count','extra-column','nondecreasing'])
def test_csv_shape_and_trend_failures(damage: str,tmp_path: Path) -> None:
    write_overview_candidate(tmp_path);path=tmp_path/CSV_PATH;rows=path.read_text(encoding='utf-8').splitlines()
    if damage=='header':rows[0]='energy,wavelength'
    elif damage=='row-count':rows.pop()
    elif damage=='extra-column':rows[3]+=',unexpected'
    else:rows[3]=rows[3].split(',')[0]+','+rows[2].split(',')[1]
    path.write_text('\n'.join(rows)+'\n',encoding='utf-8')
    with pytest.raises(OverviewFigureError):validate_overview(overview_contract(tmp_path))


@pytest.mark.parametrize('damage',['malformed','duplicate-id','empty-label','missing-label','role'])
def test_svg_structure_and_accessibility_failures(damage: str,tmp_path: Path) -> None:
    write_overview_candidate(tmp_path);path=tmp_path/SVG_PATH;text=path.read_text(encoding='utf-8')
    if damage=='malformed':text='<svg'
    elif damage=='duplicate-id':text=text.replace('id="desc"','id="title"')
    elif damage=='empty-label':text=text.replace('Decreasing trend',' ')
    elif damage=='missing-label':text=text.replace('title desc','title missing')
    else:text=text.replace('role="img"','role="presentation"')
    path.write_text(text,encoding='utf-8')
    with pytest.raises(OverviewFigureError):validate_overview(overview_contract(tmp_path))


def test_reviewed_synthetic_grid_returns_typed_artifacts(tmp_path: Path) -> None:
    write_overview_candidate(tmp_path)
    result=validate_overview(overview_contract(tmp_path))
    assert result.descriptor.package_version=='0.5.0'
    assert result.descriptor.grid.point_count==len(result.table.energies)==61
    assert result.table.wavelengths[0]==20.0  # Synthetic trend, no physics oracle.
    assert result.descriptor.generator_commit=='1'*40


def test_huge_integer_is_a_structured_input_error() -> None:
    with pytest.raises(StructuredInputError,match='finite'):finite_number(10**400,'fixture')
