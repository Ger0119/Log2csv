#!usr/bin/perl

use warnings;

@LOG = @ARGV;
%Data = ();
@DC_lst = ();
@FT_lst = ();
%Test_case = ();
%Tem_data = ();
@Lot_lst  = ();
@Test_lst = ();  

foreach $log(@LOG){
    log2csv($log);
}
$File = $LOG[0];
$File =~ s/.txt|.log/\.csv/;

open (Output,">$File");
print Output ",TestID,TestDes,Unit,L-Limit,H-Limit,".join(',',@Lot_lst)."\n";
foreach("Wno","X","Y","DUT","P/F","FailTest","BIN"){
    print Output $_.",,,,,,";
    foreach $lot(@Lot_lst){
        print Output shift @{$Data{$lot}};
        print Output ",";
    }
    print Output "\n";

}
foreach(@DC_lst,@FT_lst){
    print Output $_.',';
    print Output $Test_case{$_}.",";
    foreach $lot(@Lot_lst){
        if(scalar(@{$Data{$lot}}) != 0){
            print Output shift @{$Data{$lot}};
        }
        print Output ",";
    }
    print Output "\n";
}


close Output;


sub log2csv{
    my $file = shift;
    my $T_ID;
    my $T_Des;
    my $Value;
    my $L_Limit;
    my $H_Limit;
    my $Unit;
    my $Dut;
    my $Pin;
    my $flag;
    my $T_name;
    my $PF;
    my $Bin;

    my $flag_start = 0;
    glob @DC_lst;
    glob @FT_lst;
    glob @Lot_lst;
    glob %Test_case;
    glob @Test_lst;
    glob %Tem_data;

    open FILE,$file or die "Can not Open $file";
    while(<FILE>){
        if($_ =~ /ALARM_FAIL/){ next;}
        if($_ =~ /Start/ and $flag_start == 0){ $flag_start = 1; next}
        if($_ =~ /Start/ and $flag_start == 1){ 
            &Update_data();
        }
        chomp;
        $_ =~ s/^\s+|\s+$//g;
        unless($_ =~ /^\d/){
            if($_ =~ /^DUT\s(\d+) : (\w+) : / ){
                $Dut = $1;
                $PF  = $2;
                $Bin = $';
                $Bin =~ s/\s+/_/g;
                if($PF eq "PASS"){
                    $Tem_data{$Dut."_FailTest"} = 0;
                }
                $Tem_data{$Dut."_PF"} = $PF;
                $Tem_data{$Dut."_BIN"} = $Bin;
                if($Tem_data{$Dut."_WNO"} == 0){ next; }
                my $lot = $Tem_data{$Dut."_WNO"}.".".$Tem_data{$Dut."_XADR"}.".".$Tem_data{$Dut."_YADR"};
                unless(grep /^$lot$/,@Lot_lst){
                    push @Lot_lst,$Tem_data{$Dut."_WNO"}.".".$Tem_data{$Dut."_XADR"}.".".$Tem_data{$Dut."_YADR"};
                }
            }
            next;
        }

        @Arr = split(" ",$_);
        $len = @Arr;
        if(grep /$len/,(8,9)){
            ($T_ID,$T_Des) = @Arr[0..1];
            ($Value,$H_Limit,$L_Limit,$Unit) = get_Value(@Arr[4..6]);
            if($len == 8){ $Dut = $Arr[-1];}
            else{
                ($Dut,$Pin) = ($Arr[-2],$Arr[-1]);
                $Pin =~ s/-----//g;
            }
            $flag = "DC";
        }
        elsif(grep /$len/,(6,7)){
            ($Value,$H_Limit,$L_Limit,$Unit) = get_Value(@Arr[2..4]);
            if($len == 6){ $Dut = $Arr[-1];}
            else{
                ($Dut,$Pin) = ($Arr[-2],$Arr[-1]);
                $Pin =~ s/-----//g;
            }
            $flag = "DC";
        }
        elsif(grep /$len/,(5,3)){
            if($len == 5){
                $T_ID  = shift @Arr;
                $T_Des = shift @Arr;
            }
            ($Value,$Dut) = @Arr[1..2];
            $flag = "FT";
        }
        else{  die "Error : Data Process Miss! \n Line : $_\n" }

        $T_name = get_T_name($flag,$T_ID,$T_Des,$Pin);
        
        unless(grep /^$T_name$/,@Test_lst){
            push @Test_lst,$T_name;
        }

        if($flag eq "DC"){
            $Value = sprintf "%.1f",$Value;
            unless(grep /$T_name/,@DC_lst){
                push @DC_lst,$T_name;
            }
            unless( exists($Test_case{$T_name})){
                $Test_case{$T_name} = join(',',split('_',$T_name,2)).','.$Unit.','.$L_Limit.','.$H_Limit;
            }
        }
        elsif($flag eq "FT"){
            unless(grep /$T_name/,@FT_lst){
                push @FT_lst,$T_name;
            }
            unless( exists($Test_case{$T_name})){
                $Test_case{$T_name} = $T_ID.",".$T_Des.",,,";
            }
        }
        unless(exists($Tem_data{$Dut})){
            $Tem_data{$Dut} = $Value;
            $Tem_data{$Dut."_WNO"}  = 0;
            $Tem_data{$Dut."_XADR"} = 0;
            $Tem_data{$Dut."_YADR"} = 0;
            $Tem_data{$Dut."_BIN"}  = 0;
            $Tem_data{$Dut."_FailTest"}  = "";
        }
        else{
            $Tem_data{$Dut} .= ",".$Value;
        }
        if($T_name =~ /_WNO|_XADR|_YADR/){
            $Tem_data{$Dut.$&} = int($Value);
        }
        if($_ =~ /FAIL/){
            $Tem_data{$Dut."_FailTest"} = $T_Des;
        }
    }
    &Update_data();
}
sub Update_data{
    glob %Tem_data;
    glob %Data;
    my $lot = "";
    
    my @Duts = sort(map((grep /^\d+$/,$_),keys(%Tem_data)));
    
    foreach my $Dut(@Duts){
        $lot = $Tem_data{$Dut."_WNO"}.".".$Tem_data{$Dut."_XADR"}.".".$Tem_data{$Dut."_YADR"};
        my @arr;
        if(exists($Data{$lot})){
            if($Data{$lot} =~ /PASS/ and $Tem_data{$Dut."_PF"} eq "FAIL"){
                next;

            }
            
        }
        $Data{$lot} = \@arr;
        @arr = (@arr,$Tem_data{$Dut."_WNO"},$Tem_data{$Dut."_XADR"},$Tem_data{$Dut."_YADR"},$Dut,$Tem_data{$Dut."_PF"},$Tem_data{$Dut."_FailTest"},$Tem_data{$Dut."_BIN"});
        @arr = (@arr, sort_data(split(',',$Tem_data{$Dut})));
    }
    %Tem_data = ();
}
sub sort_data{
    my @data = @_;
    my @DC;
    my @FT;
    glob @DC_lst;
    glob @FT_lst;
    glob @Test_lst;
    
    foreach my $t(@Test_lst){
        if(scalar(@data) == 0){ last;}
        if(grep /^$t$/,@FT_lst){
            push @FT,shift @data;  
        }
        else{
            push @DC,shift @data;
        }
    }
    foreach(1..(scalar(@DC_lst)-scalar(@DC))){
        push @DC,"";
    }
    return (@DC,@FT);

}
sub get_Value{
    my $Value = shift;
    my $High  = shift;
    my $Low   = shift;
    my $High_U;
    my $Low_U;
    my $Value_U;
    my $Unit;
    
    $High  = ($High  eq "None")? "-" : $High;
    $Low   = ($Low   eq "None")? "-" : $Low;
    $Value = ($Value eq "None")? "-" : $Value;

    ($Value,$Value_U) = get_Unit($Value);
    ($High,$High_U)   = get_Unit($High);
    ($Low,$Low_U)     = get_Unit($Low);
    
    if($Low_U ne "-"){ $Unit = $Low_U; }
    elsif($High_U ne "-"){ $Unit = $High_U; }
    else{ $Unit = $Value_U; }
    
    $Value = Unit_change($Value_U,$Unit,$Value);
    $High  = Unit_change($High_U,$Unit,$High);
    $Low   = Unit_change($Low_U,$Unit,$Low);
    return $Value,$High,$Low,$Unit;
}
sub get_T_name{
    my $flag = shift;
    my $ID   = shift;
    my $Des  = shift;
    my $Pin  = shift;
    if($flag eq "FT"){ return $ID."_".$Des; }
    if($Pin eq "-----"){ return $ID."_".$Des; }
    else{ return $ID."_".$Des."_".$Pin }
}
sub get_Unit{
    my $data = shift;
    my $value;
    my $unit;
    if($data =~ /^[-.\d]+/){
        $value = $&;
        $unit = $';
    }
    if(length($unit) == 0){
        return $value,"-";
    }
    return $value,$unit;
}
sub Unit_change{
    my $before   = shift;
    my $after    = shift;
    my $value    = shift;
    my $before_U = 0;
    my $after_U  = 0;

    if($value eq "-"){ return $value; }
    if($before eq $after){ return $value; }
    my %hash = (
            'f'=> -15,
            'p'=> -12,
            'n'=> -9,
            'u'=> -6,
            'm'=> -3,
            'K'=> 3,
            'M'=> 6,
            'G'=> 9,
            '-'=> 0,
    );
    if( exists($hash{substr($before,0,1)})){
        $before_U = $hash{substr($before,0,1)};
    }
    if( exists($hash{substr($after,0,1)})){
        $after_U = $hash{substr($after,0,1)};
    }
    return $value * 10 ** ($before_U - $after_U);
}
