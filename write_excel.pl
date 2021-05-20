#!usr/bin/perl

use warnings;
use Excel::Writer::XLSX;
use POSIX qw(strftime);
use Win32::OLE qw(in with);
use Win32::OLE::Const 'Microsoft Excel';
use Cwd;

$dir = getcwd;
$Win32::OLE::Warn = 3;
$Excel = Win32::OLE->GetActiveObject('Excel.Application')|| Win32::OLE->new('Excel.Application', 'Quit');  # get already active Excel
$Excel->{DisplayAlerts}=0;  

$exl = 'LFT_base.xlsx';
system('copy .\Base\\'.$exl.' .\\');

while(<*.csv>){
    $file = $_;
}
$Lot = get_lot($file,$exl);
$new_name = get_new_name($Lot,$file);

$Book  = $Excel->Workbooks->Open($dir.'/'.$exl);
$Sheet = $Book->Worksheets(1);

open FILE,$file;
@Data = <FILE>;
close FILE;

@Dut = get_data($Data[4]);
@result = get_data($Data[6]);
@Bin = get_data($Data[7]);

$Sheet->Cells(2,5)->{Value} = $Lot;

&write_excel($Sheet,5,254,@Dut);
&write_excel($Sheet,4,8,@result);
&write_excel($Sheet,8,254,@Bin);

$Book->Save;
$Book->Close;

system('move '.$exl.' '.$new_name);

sub get_data{
    my $line = shift @_;
    chomp($line);
    my @data = split(',',$line);
    foreach(1..6){
        shift @data;
    }
    return @data;
}

sub write_excel{
    my $sheet = shift @_;
    my $row = shift @_;
    my $col = shift @_;
    my @data = @_;

    foreach(@data){
        $sheet->Cells($row,$col++)->{Value} = $_;
    }

}
sub get_lot{
    my $line = shift;
    my $head = shift;

    $head =~ s/_base.xlsx//;
    if($line =~ /_(\d{4}[KI]P[SR0-9]\d{2})_/){
        return $head.'-'.$1;
    }
    else{
        print "\n\nLot get Error!!\n\n";
        exit();
    }

}
sub get_new_name{
    my $lot = shift;
    my $csv = shift;
    my $test = "";
    if($csv =~ /^([^_]+)/){
        $test = $1;
    }
    my $time = strftime "%Y%m%d",localtime;
    return $test.'_'.$lot.'_'.$time.'.xlsx';

}
